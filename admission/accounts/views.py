# -*- coding: utf-8 -*-
from django.http import JsonResponse
from rest_framework import views, generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from .authentication import BearerAuthentication
from .serializers import CustomUserSerializer

from .models import CustomUser


class UserRetriaveAPIView(views.APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get(self, request):
        user = request.user
        return JsonResponse(data=self.serializer_class(user).data, status=200)
