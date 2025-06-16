"""
ASGI config for admission project.
"""

import os
from django.core.asgi import get_asgi_application

# Важно: сначала устанавливаем переменные окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admission.settings')

# Инициализируем Django
django_asgi_app = get_asgi_application()

# Только ПОСЛЕ инициализации Django импортируем остальное
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer
from peopleQueue.schema import schema

class CustomGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        # Разрешаем подключения без аутентификации
        # Для публичного табло это необходимо
        await super().connect()
        
        # Для отладки можно добавить лог
        print(f"WebSocket connected: {self.scope['client']}")

gql_ws_consumer = CustomGraphQLWSConsumer.as_asgi(schema=schema)

websocket_urlpatterns = [
    re_path(r"^graphql/$", gql_ws_consumer),  # Используйте ^ и $ для точного соответствия
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(  # Добавляем валидацию хостов
        AuthMiddlewareStack(  # Оставляем middleware аутентификации
            URLRouter(websocket_urlpatterns)
        )
    ),
})
