"""
ASGI config for admission project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "admission.settings",
)

# Django необходимо инициализировать до импортов schema,
# routing и middleware, которые обращаются к моделям.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer

from peopleQueue.middleware import TokenAuthMiddleware
from peopleQueue.routing import websocket_urlpatterns as operator_websocket_urlpatterns
from peopleQueue.schema import schema


class CustomGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        await super().connect()

        client = self.scope.get("client")
        print(f"GraphQL WebSocket connected: {client}")


gql_ws_consumer = CustomGraphQLWSConsumer.as_asgi(schema=schema)

websocket_urlpatterns = [
    re_path(r"^graphql/$", gql_ws_consumer),
    *operator_websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                TokenAuthMiddleware(
                    URLRouter(websocket_urlpatterns)
                )
            )
        ),
    }
)
