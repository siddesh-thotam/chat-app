# Leave group view
from django.contrib.auth import get_user_model
from django.shortcuts import render , get_object_or_404 , redirect
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import ValidationError
from .models import *
from .forms import *


# Create your views here.

# views.py - Fixed chat_view function
@login_required
def chat_view(request, chatroom_name="public-chat"):
    # Ensure the public-chat group exists
    if chatroom_name == "public-chat":
        chat_group, created = ChatGroup.objects.get_or_create(
            group_name="public-chat", 
            defaults={"groupchat_name": "Public Chat"}
        )
    else:
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    # Only include messages that have either body or file
    valid_messages = chat_group.chat_messages.order_by('-created').filter(
        models.Q(body__isnull=False, body__gt='') | models.Q(file__isnull=False)
    )[:30]
    chat_messages = reversed(valid_messages)
    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, "You need to first verify your email to join a chat.")
                return redirect('profile-settings')

    # HTMX request handling with improved validation
    if request.htmx:
        form = ChatmessageCreateForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            
            # Get cleaned data and check for empty content
            body_content = form.cleaned_data.get('body', '').strip()
            file_content = request.FILES.get('file')
            
            # Prevent saving if both body and file are empty
            if not body_content and not file_content:
                return HttpResponse(status=204)  # No content
            
            # Only set body if it's not empty
            if body_content:
                message.body = body_content
                
            # Handle file upload if present
            if file_content:
                message.file = file_content
            
            try:
                message.save()
                context = {
                    'message': message,
                    'user': request.user,
                }
                return render(request, 'a_rtchat/partials/chat_message_p.html', context)
            except ValidationError as e:
                # Handle validation errors (e.g., empty message)
                return HttpResponse(status=204)
            except Exception as e:
                # Handle other errors
                print(f"Error saving message: {e}")
                return HttpResponse(status=500)
        else:
            # Form is invalid
            return HttpResponse(status=400)

    chatroom_name = chat_group.group_name
    context = {
        'chat_messages': chat_messages,
        'form': form,
        'other_user': other_user,
        'chatroom_name': chat_group.group_name,
        'chat_group': chat_group
    }
    
    return render(request, 'a_rtchat/chat.html', context)

@login_required
def get_or_create_chatroom(request , username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username = username)
    my_private_chatrooms = request.user.chat_groups.filter(is_private=True)
    
    if my_private_chatrooms.exists():
        for chatroom in my_private_chatrooms:
            if other_user in chatroom.members.all():
                return redirect('chatroom', chatroom.group_name)
   
    chatroom = ChatGroup.objects.create( is_private = True )
    chatroom.members.add(other_user, request.user)   
    return redirect('chatroom', chatroom.group_name)

# In a context processor or in your main view
def chat_dropdown_context(request):
    user = request.user
    online_status = {}
    private_chat_users = set()
    if not user.is_authenticated:
        return {'online_status': online_status, 'private_chat_users': []}

    # Public chat
    try:
        public_chat = ChatGroup.objects.get(group_name='public-chat')
        public_online = public_chat.users_online.exclude(id=user.id).exists()
        online_status['public-chat'] = public_online
    except ChatGroup.DoesNotExist:
        online_status['public-chat'] = False

    # Group chats
    for group in user.chat_groups.all():
        key = f'group-{group.id}'
        online_status[key] = group.users_online.exclude(id=user.id).exists()

    # Private chats (users you've chatted with)
    User = get_user_model()
    for group in ChatGroup.objects.filter(is_private=True, members=user):
        for member in group.members.exclude(id=user.id):
            private_chat_users.add(member)
    private_chat_users = list(private_chat_users)
    for other in private_chat_users:
        key = f'user-{other.username}'
        online_status[key] = other.online_in_groups.exclude(id=user.id).exists()

    return {'online_status': online_status, 'private_chat_users': private_chat_users}

@login_required
def create_groupchat(request):
    form = NewGroupForm()
    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom' , new_groupchat.group_name)
        



    context={
        'form' : form
    }
    return render(request , 'a_rtchat/create_groupchat.html' ,context)

@login_required
def chatroom_edit_view(request ,chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    form = ChatRoomEditForm(instance=chat_group)
    if request.method == 'POST':
        form = ChatRoomEditForm(request.POST , instance=chat_group)
        if form.is_valid():
            form.save()

            remove_members = request.POST.getlist('remove_members')
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)
            return redirect('chatroom' , chatroom_name)

    context={
        'form':form,
        'chat_group':chat_group
    }
    return render(request , 'a_rtchat/chatroom_edit.html' , context)

@login_required
def chatroom_delete_view(request , chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        return Http404()
    
    if request.method == 'POST':
        chat_group.delete()
        messages.success(request , "Chatroom Deleted Successfully.")
        return redirect('home')
    
    context={
        'chat_group': chat_group,
    }


    return render(request , 'a_rtchat/delete_chatroom.html', context)

@login_required
def leave_group_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    user = request.user
    if user == chat_group.admin:
        messages.error(request, "Admin cannot leave the group. Transfer admin or delete the group.")
        return redirect('chatroom', chatroom_name)
    if user not in chat_group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('chatroom', chatroom_name)
    if request.method == 'POST':
        chat_group.members.remove(user)
        messages.success(request, "You have left the group.")
        return redirect('home')
    return render(request, 'a_rtchat/leave_group_confirm.html', {'chat_group': chat_group})

# ...existing code...
def chat_file_upload(request , chatroom_name):
    chat_group = get_object_or_404(ChatGroup , group_name=chatroom_name)
    if request.htmx and request.FILES:
        file = request.FILES.get('file')
        # Only create message if file is present and not empty
        if file and getattr(file, 'size', 0) > 0:
            message = GroupMessage(file=file, author=request.user, group=chat_group)
            message.save()
            channel_layer = get_channel_layer()
            event={
                'type' : 'chat.message',
                'message_id':message.id,
            }
            async_to_sync(channel_layer.group_send)(
                chatroom_name, event
            )
            # Return the rendered message HTML for HTMX
            context = {
                'message': message,
                'user': request.user,
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)
    return HttpResponse()