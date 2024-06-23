from rest_framework import serializers
from django.contrib.auth.models import Group

from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = CustomUser
        # fields = "__all__"
        exclude = ['password']
