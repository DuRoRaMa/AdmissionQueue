import logging
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer

from accounts.authentication import BearerAuthentication
from . import models
from . import serializers

# Create your views here.


class HelperListAPIView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Helper.objects.filter(is_active=True)
    serializer_class = serializers.HelperSerializer


class HelpRequestCreateAPIView(generics.CreateAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.HelpRequest.objects.all()
    serializer_class = serializers.HelpRequestSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
