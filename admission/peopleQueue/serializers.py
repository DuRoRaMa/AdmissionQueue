from rest_framework import serializers

from .models import Talon


class TalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Talon
        fields = ('name',)
