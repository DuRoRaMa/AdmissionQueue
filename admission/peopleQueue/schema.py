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


class TalonActionType(DjangoObjectType):
    class Meta:
        model = models.TalonAction
        fields = "__all__"


class TalonLogType(DjangoObjectType):
    class Meta:
        model = models.TalonLog
        fields = "__all__"


class Query(graphene.ObjectType):
    talon = graphene.List(TalonType)
    talon_log = graphene.Field(TalonLogType)

    def resolve_talon(root, info):
        return models.Talon.objects.all()

    def resolve_talon_log(root, info):
        return models.TalonLog.objects.last()


schema = graphene.Schema(query=Query)
