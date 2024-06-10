import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from . import models


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'operator_settings']


class OperatorSettingsType(DjangoObjectType):
    class Meta:
        model = models.OperatorSettings
        fields = '__all__'


class OperatorLocationType(DjangoObjectType):
    class Meta:
        model = models.OperatorLocation
        fields = '__all__'


class TalonType(DjangoObjectType):
    class Meta:
        model = models.Talon
        fields = "__all__"


class TalonPurposesType(DjangoObjectType):
    class Meta:
        model = models.TalonPurposes
        fields = "__all__"


class TalonLogType(DjangoObjectType):
    class Meta:
        model = models.TalonLog
        fields = "__all__"


class Query(graphene.ObjectType):
    talons = graphene.List(TalonType)
    talon_log = graphene.Field(TalonLogType)
    talon_log_by_id = graphene.Field(
        TalonLogType, id=graphene.Int(required=True))
    talon_by_id = graphene.Field(TalonType, id=graphene.Int(required=True))
    count_active_talons = graphene.Int()

    def resolve_count_active_talons(root, info):
        return models.Talon.get_active_queryset().count()

    def resolve_talon_by_id(root, info, id):
        return models.Talon.objects.get(pk=id)

    async def resolve_talons(root, info):
        return models.Talon.get_active_queryset().filter(compliting=True)

    async def resolve_talon_log_by_id(root, info, id):
        return models.TalonLog.objects.get(pk=id)

    async def resolve_talon_log(root, info):
        return models.TalonLog.objects.last()


schema = graphene.Schema(query=Query)
