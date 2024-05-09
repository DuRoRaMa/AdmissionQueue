"""
ASGI config for admission project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""
if True:
    import django
    django.setup()

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from peopleQueue.routing import websocket_urlpatterns


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admission.settings.local")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(
        websocket_urlpatterns
    )),
})
