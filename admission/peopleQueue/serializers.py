from attr import fields
from rest_framework import serializers

from . import models


class TalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Talon
        fields = "__all__"
        read_only_fields = ("name", "ordinal")


class TalonPurposesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TalonPurposes
        fields = "__all__"


class OperatorSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OperatorSettings
        fields = '__all__'


class TalonLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TalonLog
        fields = "__all__"


class OperatorLocationSerializer(serializers.ModelSerializer):
    settings = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.OperatorLocation
        fields = "__all__"
