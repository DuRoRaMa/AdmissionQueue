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

    def create(self, validated_data):
        ret: models.OperatorSettings = super().create(validated_data)
        user = ret.user
        if ret.automatic_assignment:
            for purpose in ret.purposes.all():
                models.OperatorQueue(user=user, purpose=purpose).save()
        else:
            models.OperatorQueue.objects.filter(user=user).delete()

        return ret

    def update(self, instance: models.OperatorSettings, validated_data):
        user = instance.user
        models.OperatorQueue.objects.filter(user=user).delete()
        if validated_data.get("automatic_assignment"):
            for purpose in validated_data.get("purposes"):
                models.OperatorQueue(user=user, purpose=purpose).save()

        ret: models.OperatorSettings = super().update(instance, validated_data)
        return ret


class TalonLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TalonLog
        fields = "__all__"


class OperatorLocationSerializer(serializers.ModelSerializer):
    settings = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.OperatorLocation
        fields = "__all__"
