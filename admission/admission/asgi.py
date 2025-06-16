"""
ASGI config for admission project.
"""

import os
from django.core.asgi import get_asgi_application

# Важно: сначала устанавливаем переменные окружения ДО импорта других модулей Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admission.settings')

# Получаем ASGI-приложение для HTTP
django_asgi_app = get_asgi_application()

# Только ПОСЛЕ инициализации Django импортируем остальные модули
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer
from peopleQueue.schema import schema

class CustomGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        if not self.scope.get("user"):
            await self.close(code=4401)
            return
        await super().connect()

gql_ws_consumer = CustomGraphQLWSConsumer.as_asgi(schema=schema)

websocket_urlpatterns = [
    re_path(r"^graphql/$", gql_ws_consumer),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
