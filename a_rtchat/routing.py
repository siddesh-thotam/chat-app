from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Allow trailing slash
    re_path(r"^ws/chatroom/(?P<chatroom_name>[\w\-]+)/$", consumers.ChatroomConsumer.as_asgi()),

    # Online status
    re_path(r"^ws/online-status/$", consumers.OnlineStatusConsumer.as_asgi()),
]
