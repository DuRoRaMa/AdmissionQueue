from attr import fields
from rest_framework import serializers

from . import models


class TalonLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TalonLog
        fields = "__all__"


class TalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Talon
        fields = "__all__"
        read_only_fields = ("name", "ordinal", 'comment')


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
            if ret.user.is_assigned_talon():
                ret.user.assign_talon()
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
        if validated_data.get("automatic_assignment") and not user.is_assigned_talon():
            ret.user.assign_talon()
        return ret


class OperatorLocationSerializer(serializers.ModelSerializer):
    settings = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.OperatorLocation
        fields = "__all__"
