import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer
from peopleQueue.schema import schema

django_asgi_app = get_asgi_application()
gql_ws_consumer = GraphQLWSConsumer.as_asgi(schema=schema)

websocket_urlpatterns = [
    re_path(r"graphql/?$", gql_ws_consumer),  # Обрабатывает /graphql и /graphql/
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
