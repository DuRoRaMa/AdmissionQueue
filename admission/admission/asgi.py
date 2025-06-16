"""
ASGI config for admission project.
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer
from peopleQueue.schema import schema

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admission.settings')
django.setup()

# WebSocket consumer
class CustomGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        # Дополнительная проверка аутентификации
        if not self.scope.get("user", None):
            await self.close(code=4401)  # Unauthorized
            return
        await super().connect()

gql_ws_consumer = CustomGraphQLWSConsumer.as_asgi(schema=schema)

websocket_urlpatterns = [
    re_path(r"^graphql/$", gql_ws_consumer),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
