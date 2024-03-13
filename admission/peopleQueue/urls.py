# -*- coding: utf-8 -*-
from django.urls import re_path

from .views import OperatorView, RegisterTalonView, TabloView, TalonAPIView
 
 
app_name = 'queue'
urlpatterns = [
    re_path(r"^register", RegisterTalonView.as_view(), name="RegTalon"),
    re_path(r"^operator", OperatorView.as_view(), name="OperatorPage"),
    re_path(r"^talon/api", TalonAPIView.as_view(), name="TalonAPI"),
    re_path(r"^tablo", TabloView.as_view(), name="TabloPage"),
]