from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user_by_token(token_key: str):
    try:
        token = Token.objects.select_related("user").get(key=token_key)
    except Token.DoesNotExist:
        return AnonymousUser()

    if not token.user.is_active:
        return AnonymousUser()

    return token.user


class TokenAuthMiddleware(BaseMiddleware):
    """
    Авторизация Channels через DRF TokenAuthentication.

    Клиент передаёт токен в query string:
    /ws/operator/notifications/?token=<token>

    Если токен не передан, пользователь из AuthMiddlewareStack сохраняется.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token_key = params.get("token", [None])[0]

        if token_key:
            scope["user"] = await get_user_by_token(token_key)

        return await super().__call__(scope, receive, send)
