from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Talon

# Create your views here.
@login_required
def RegisterTalon(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            talon = Talon.objects.create(**form.cleaned_data)
            return HttpResponse(str(talon))
    else:
        form = RegisterForm()

    return render(request, "RegisterTalon.html", {"form": form})
