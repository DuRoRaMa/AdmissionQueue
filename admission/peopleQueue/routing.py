from django.urls import re_path
from .consumers import AsyncChatConsumer

websocket_urlpatterns = [
   re_path(r'ws/chat/$', AsyncChatConsumer.as_asgi()),
]