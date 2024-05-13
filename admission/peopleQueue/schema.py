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
    talon_by_id = graphene.Field(TalonType, id=graphene.Int(required=True))

    def resolve_talon_by_id(root, info, id):
        return models.Talon.objects.get(pk=id)

    def resolve_talons(root, info):
        return models.Talon.objects.filter(logs__action=models.TalonLog.Actions.STARTED).exclude(logs__action__in=[models.TalonLog.Actions.COMPLETED, models.TalonLog.Actions.CANCELLED])

    def resolve_talon_log(root, info):
        if type(info.context) == dict:
            return info.context.get('talonLog')
        return models.TalonLog.objects.last()


schema = graphene.Schema(query=Query)
