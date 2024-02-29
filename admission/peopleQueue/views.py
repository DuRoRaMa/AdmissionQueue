from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from rest_framework import generics

from .serializers import TalonSerializer
from .forms import RegisterForm
from .models import Talon


class RegisterTalon(LoginRequiredMixin, View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "RegisterTalon.html", {"form": form})
    
class Operator(LoginRequiredMixin, View):
    def get(self, request):
        pass

class TalonAPIView(generics.CreateAPIView):
    queryset = Talon.objects.all()
    serializer_class = TalonSerializer
    
    def perform_create(self, serializer):
        serializer.save()
        messages.info(self.request, "Talon created successfully")
    