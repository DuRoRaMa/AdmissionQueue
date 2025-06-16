import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import re_path
from strawberry.django.views import AsyncGraphQLView
from peopleQueue.schema import schema

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    re_path(r"graphql/?$", AsyncGraphQLView.as_asgi(
        schema=schema,
        subscriptions_enabled=True
    )),
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
