import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatGroup, GroupMessage

# Track online users by username
ONLINE_USERS = {}

class ChatroomConsumer(AsyncWebsocketConsumer):
    """Production-ready WebSocket consumer with proper timeout handling"""

    async def connect(self):
        """Handle WebSocket connection with timeout protection"""
        try:
            # Set connection timeout
            await asyncio.wait_for(self._connect_internal(), timeout=15.0)
        except asyncio.TimeoutError:
            print("[ERROR] WebSocket connection timeout")
            await self.close(code=1011)  # Internal error code
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            await self.close(code=1011)

    async def _connect_internal(self):
        """Internal connection method"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close(code=4000)  # Custom close code for auth failure
            return

        self.chatroom_name = self.scope["url_route"]["kwargs"]["chatroom_name"]
        
        # Accept connection immediately
        await self.accept()
        
        # Add to channel group
        await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
        
        # Get chatroom info with timeout
        try:
            await asyncio.wait_for(self._setup_chatroom(), timeout=10.0)
        except asyncio.TimeoutError:
            print("[WARNING] Chatroom setup timed out, but connection remains open")
        except Exception as e:
            print(f"[ERROR] Chatroom setup failed: {e}")

    @database_sync_to_async
    def _setup_chatroom_sync(self):
        """Sync method for chatroom setup"""
        chatroom = ChatGroup.objects.filter(group_name=self.chatroom_name).first()
        if chatroom and not chatroom.users_online.filter(id=self.user.id).exists():
            chatroom.users_online.add(self.user)
        return chatroom

    async def _setup_chatroom(self):
        """Setup chatroom after connection is established"""
        self.chatroom = await self._setup_chatroom_sync()
        
        if not self.chatroom:
            print(f"[ERROR] Chatroom {self.chatroom_name} not found")
            return

        await self._update_online_count()

    async def disconnect(self, close_code):
        """Handle disconnection with proper cleanup"""
        try:
            if hasattr(self, 'chatroom_name'):
                await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)

            # Cleanup user from online list
            if hasattr(self, 'chatroom') and hasattr(self, 'user'):
                await self._remove_user_from_online()
                    
        except Exception as e:
            print(f"[ERROR] Disconnect cleanup failed: {e}")

    @database_sync_to_async
    def _remove_user_from_online(self):
        """Sync method to remove user from online list"""
        if self.chatroom.users_online.filter(id=self.user.id).exists():
            self.chatroom.users_online.remove(self.user)

    async def receive(self, text_data):
        """Handle incoming messages with error handling"""
        try:
            data = json.loads(text_data)
            if data.get("type") == "seen":
                await self._handle_seen()
            elif data.get("body"):
                await self.handle_message(data["body"])
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON received")
        except Exception as e:
            print(f"[ERROR] Message processing failed: {e}")

    @database_sync_to_async
    def create_message_sync(self, body):
        """Sync method to create message"""
        return GroupMessage.objects.create(
            body=body, author=self.user, group=self.chatroom
        )

    async def handle_message(self, body):
        """Handle new message creation"""
        if not hasattr(self, 'chatroom'):
            return
            
        message = await self.create_message_sync(body)
        
        # Send to all group members
        await self.channel_layer.group_send(
            self.chatroom_name,
            {
                "type": "chat.message",
                "message_id": message.id,
                "username": self.user.username,
            }
        )

    @database_sync_to_async
    def handle_seen_sync(self):
        """Sync method to mark messages as seen"""
        unseen_messages = GroupMessage.objects.filter(
            group=self.chatroom
        ).exclude(seen_by=self.user)
        
        for msg in unseen_messages:
            msg.seen_by.add(self.user)

    async def _handle_seen(self):
        """Mark messages as seen"""
        if not hasattr(self, 'chatroom'):
            return
        await self.handle_seen_sync()

    @database_sync_to_async
    def get_message_data_sync(self, message_id):
        """Sync method to get message data"""
        try:
            message = GroupMessage.objects.select_related('author').get(id=message_id)
            
            # Check if message has valid content
            if not message.body and not message.file:
                return None
                
            message_data = {
                "message_id": message.id,
                "username": message.author.username,
                "timestamp": message.created.isoformat(),
            }
            
            # Add body only if it exists and is not empty
            if message.body and message.body.strip():
                message_data["message"] = message.body.strip()
            elif message.file:
                # For file messages, send a descriptive text
                message_data["message"] = f"Shared a file: {message.filename}"
            else:
                return None
                
            return message_data
            
        except GroupMessage.DoesNotExist:
            return None

    async def chat_message(self, event):
        """Send message to client"""
        try:
            message_data = await self.get_message_data_sync(event["message_id"])
            
            if not message_data:
                print(f"[WARNING] Empty or invalid message with ID {event.get('message_id')}")
                return
                
            message_data["type"] = "message"
            await self.send(text_data=json.dumps(message_data))
            
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

    @database_sync_to_async
    def get_online_count_sync(self):
        """Sync method to get online count"""
        return self.chatroom.users_online.count()

    async def _update_online_count(self):
        """Update online count for all users"""
        try:
            if hasattr(self, 'chatroom'):
                online_count = await self.get_online_count_sync()
                
                await self.channel_layer.group_send(
                    self.chatroom_name,
                    {
                        "type": "online.count",
                        "online_count": online_count,
                    }
                )
        except Exception as e:
            print(f"[ERROR] Online count update failed: {e}")

    async def online_count(self, event):
        """Send online count update"""
        await self.send(text_data=json.dumps({
            "type": "online_count",
            "online_count": event["online_count"],
        }))

    # consumers.py - Add this method to ChatroomConsumer class
    async def message_handler(self, event):
        """Handle message_handler type messages (for file uploads)"""
        try:
            message_data = await self.get_message_data_sync(event["message_id"])
            
            if not message_data:
                print(f"[WARNING] Empty or invalid message with ID {event.get('message_id')}")
                return
                
            message_data["type"] = "message"
            await self.send(text_data=json.dumps(message_data))
            
        except Exception as e:
            print(f"[ERROR] Failed to handle message: {e}")


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    """Online status consumer for production"""

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = "online_status"

        # Add to online tracking
        if self.user.username not in ONLINE_USERS:
            ONLINE_USERS[self.user.username] = set()
        ONLINE_USERS[self.user.username].add(self.channel_name)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Broadcast updated online count to all clients
        await self._broadcast_online_count()

    async def disconnect(self, close_code):
        if self.user.username in ONLINE_USERS:
            ONLINE_USERS[self.user.username].discard(self.channel_name)
            if not ONLINE_USERS[self.user.username]:
                del ONLINE_USERS[self.user.username]

        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        # Broadcast updated online count to all clients
        await self._broadcast_online_count()

    async def receive(self, text_data):
        # Keep connection alive
        await self.send(text_data=json.dumps({"type": "pong"}))

    async def _broadcast_online_count(self):
        # Count unique online users
        online_count = len(ONLINE_USERS)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "online.count",
                "online_count": online_count,
            }
        )

    async def online_count(self, event):
        await self.send(text_data=json.dumps({
            "type": "online_count",
            "online_count": event["online_count"],
        }))