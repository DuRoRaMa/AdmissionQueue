from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from rest_framework import generics
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .serializers import TalonSerializer
from .forms import RegisterForm
from .models import Talon


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

class TalonAPIView(LoginRequiredMixin, generics.CreateAPIView):
    queryset = Talon.objects.all()
    serializer_class = TalonSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
        messages.info(self.request, "Talon created successfully")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "chat_message",  
                "message": serializer.data['name']
            }
        )
    