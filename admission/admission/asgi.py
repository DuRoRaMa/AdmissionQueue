"""
ASGI config for admission project.
"""

import os

from django.core.asgi import get_asgi_application

# Не перезаписывает значение, если manage.py уже установил settings_dev
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "admission.settings",
)

# Django должен быть инициализирован до импорта schema и routing
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer

from peopleQueue.schema import schema


class CustomGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        await super().connect()

        client = self.scope.get("client")
        print(f"WebSocket connected: {client}")


gql_ws_consumer = CustomGraphQLWSConsumer.as_asgi(schema=schema)


websocket_urlpatterns = [
    re_path(r"^graphql/$", gql_ws_consumer),
]


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,

        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)