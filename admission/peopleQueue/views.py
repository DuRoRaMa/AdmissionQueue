import datetime
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .serializers import TalonSerializer
from .forms import RegisterForm
from .models import Talon

channel_layer = get_channel_layer()

class RegisterTalonView(LoginRequiredMixin, View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "RegisterTalon.html", {"form": form})
    
class OperatorView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "Operator.html", {})

class TabloView(View):
    def get(self, request):
        return render(request, "Tablo.html", {})
    
class OperatorAPIView(LoginRequiredMixin, APIView):
    def get(self, request):
        talon = Talon.objects.filter(completed=False, compliting_by__isnull=True).order_by("created_at")[0]
        talon.compliting_by = self.request.user
        talon.save()
        serializer = TalonSerializer(talon)
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "talon_update",
                "message": serializer.data
            }
        )
        return Response(serializer.data, status=200)
    
    def post(self, request):
        talon = self.request.user.compliting_talon
        if talon is None:
            return Response(data={"errors":['You do not do talon right now']}, status=400)
        talon.completed = True
        talon.completed_at = datetime.datetime.now()
        talon.completed_by = self.request.user
        talon.compliting_by = None;
        talon.save()
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "talon_remove",
                "message": TalonSerializer(talon).data
            }
        )
        return Response(status=200)
        

class TalonListCreateAPIView(LoginRequiredMixin, generics.ListCreateAPIView):
    queryset = Talon.objects.filter(completed=False).order_by('created_at')
    serializer_class = TalonSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
        messages.info(self.request, "Talon created successfully")
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "talon_create",
                "message": serializer.data
            }
        )
    
    