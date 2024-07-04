from strawberry import type, Schema
from strawberry_django.optimizer import DjangoOptimizerExtension
from .main import Query as QMain, Subscription as SMain


@type
class Subscription(SMain):
    pass


@type
class Query(QMain):
    pass


schema = Schema(
    query=Query,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension]
)
