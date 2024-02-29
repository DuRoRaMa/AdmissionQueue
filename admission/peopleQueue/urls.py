# -*- coding: utf-8 -*-
from django.urls import re_path
 
from .views import RegisterTalon, TalonAPIView
 
app_name = 'queue'
urlpatterns = [
    re_path(r"^register", RegisterTalon.as_view(), name="RegTalon"),
    re_path(r"^talon/api", TalonAPIView.as_view(), name="TalonAPI"),
]