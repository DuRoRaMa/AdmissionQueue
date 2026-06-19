from rest_framework import serializers
from django.contrib.auth import get_user_model

from . import models


class HelperUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name"]


class HelperSerializer(serializers.ModelSerializer):
    user = HelperUserSerializer(read_only=True)

    class Meta:
        model = models.Helper
        fields = "__all__"


class HelpThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpTheme
        fields = "__all__"


class HelpRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HelpRequest
        fields = "__all__"


class MaxHelperLinkSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20, trim_whitespace=True)
    external_user_id = serializers.CharField(max_length=255, trim_whitespace=True)


class MaxExternalUserSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(max_length=255, trim_whitespace=True)