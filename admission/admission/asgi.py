import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from strawberry.channels import GraphQLWSConsumer
from peopleQueue.schema import schema
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admission.settings')
django.setup()

class AuthenticatedGraphQLWSConsumer(GraphQLWSConsumer):
    async def connect(self):
        try:
            # Получаем токен из query string или cookies
            query_params = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_params:
                token = query_params.split('token=')[1].split('&')[0]
            elif 'headers' in self.scope:
                headers = dict(self.scope['headers'])
                if b'cookie' in headers:
                    cookies = headers[b'cookie'].decode().split(';')
                    for cookie in cookies:
                        if 'auth_token=' in cookie.strip():
                            token = cookie.strip().split('auth_token=')[1]
                            break
            
            if not token:
                logger.warning("No token provided in WebSocket connection")
                await self.close(code=4403)  # Unauthorized
                return

            # Валидация токена
            Fernet(os.environ['FERNET_KEY']).decrypt(token.encode())
            
            await super().connect()
            logger.info(f"WebSocket connection established for {self.scope['user']}")

        except InvalidToken:
            logger.error("Invalid token in WebSocket connection")
            await self.close(code=4401)  # Unauthorized
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close(code=4400)  # Internal Server Error

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                re_path(r"^graphql/?$", AuthenticatedGraphQLWSConsumer.as_asgi(schema=schema)),
            ])
        )
    ),
})
