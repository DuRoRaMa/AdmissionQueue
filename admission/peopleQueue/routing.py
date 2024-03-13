from django.urls import re_path
from .consumers import AsyncTabloConsumer

websocket_urlpatterns = [
    re_path(r"^ws/tablo", AsyncTabloConsumer.as_asgi(), name="WSTablo"),
]