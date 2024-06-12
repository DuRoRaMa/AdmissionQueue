import json
from typing import AsyncGenerator, Optional
from django.db.models.manager import BaseManager
import strawberry
import strawberry.django
from strawberry.channels.handlers.ws_handler import GraphQLWSConsumer
import strawberry_django
from strawberry_django.optimizer import DjangoOptimizerExtension
from django.contrib.auth import get_user_model
from . import models


@strawberry_django.type(models.OperatorLocation, fields='__all__')
class OperatorLocation:
    pass


@strawberry_django.type(models.OperatorSettings, fields='__all__')
class OperatorSettings:
    location: OperatorLocation


@strawberry_django.type(get_user_model(), fields=['id', 'username', 'first_name', 'last_name'])
class User:
    operator_settings: Optional[OperatorSettings]


@strawberry_django.type(models.TalonPurposes, fields='__all__')
class TalonPurposes:
    pass


@strawberry_django.type(models.Talon, fields='__all__')
class Talon:
    logs: list["TalonLog"]
    purpose: TalonPurposes


@strawberry_django.type(models.TalonLog, fields='__all__')
class TalonLog:
    talon: Talon
    created_by: User


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def talonLogs(self, info: strawberry.Info) -> AsyncGenerator[TalonLog, None]:
        ws: GraphQLWSConsumer = info.context["ws"]
        channel_layer = ws.channel_layer
        await channel_layer.group_add("tablo", ws.channel_name)  # type: ignore
        async with ws.listen_to_channel('talonLog.create', groups=['tablo']) as cm:
            async for message in cm:
                yield await models.TalonLog.objects.aget(pk=message['message'])


@strawberry.type
class Query:
    talons: list[Talon] = strawberry_django.field()
    talon: Talon = strawberry_django.field()

    @strawberry.field
    def tabloTalons(self) -> list[Talon]:
        return models.Talon.objects.filter(compliting=True).order_by('-updated_at')

    @strawberry.field
    async def countActiveTalons(self) -> int:
        return await models.Talon.objects.filter(compliting=True).acount()

    @strawberry.field
    async def lastTalonLog(self) -> TalonLog:
        return await models.TalonLog.objects.alast()  # type: ignore


schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension]
)
