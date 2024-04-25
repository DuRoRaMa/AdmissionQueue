# -*- coding: utf-8 -*-
from django.urls import re_path, path

from . import views

app_name = 'queue'
urlpatterns = [
    re_path(r"^operator/", views.OperatorAPIView.as_view(), name="OperatorAPI"),
    re_path(r"^talon/", views.TalonListCreateAPIView.as_view(), name="TalonAPI"),
    re_path(r"^location/", views.OperatorLocationListAPIView.as_view()),
    re_path(r"^settings/",
            views.OperatorSettingsAPIView.as_view()),
    re_path(r"^purposes/", views.TalonPurposesListAPIView.as_view()),
    re_path(r"tablo/", views.TabloAPIView().as_view())
]
