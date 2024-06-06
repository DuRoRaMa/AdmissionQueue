from rest_framework import serializers
from . import models


class HelperSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Helper
        fields = "__all__"


class HelpRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpRequest
        fields = "__all__"
