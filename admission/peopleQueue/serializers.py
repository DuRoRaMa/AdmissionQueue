from attr import fields
from rest_framework import serializers

from .models import OperatorLocation, OperatorSettings, Talon, TalonPurposes


class TalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Talon
        fields = "__all__"


class TalonPurposesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalonPurposes
        fields = "__all__"


class OperatorSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorSettings
        fields = '__all__'


class OperatorLocationSerializer(serializers.ModelSerializer):
    settings = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = OperatorLocation
        fields = "__all__" 
