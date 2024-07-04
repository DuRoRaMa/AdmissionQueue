# -*- coding: utf-8 -*-
from django.urls import re_path, path, include

from . import views

app_name = 'queue'
urlpatterns = [
    re_path(r"^info", views.OperatorInfoListAPIView.as_view()),
    re_path(r"^talon/", views.TalonListCreateAPIView.as_view()),
    re_path(r"^operator/", include([
            re_path(r"^talon/action", views.OperatorTalonActionAPIView.as_view()),
            re_path(r"^settings", views.OperatorSettingsAPIView.as_view(),
                    name='operator-settings'),
            re_path(r"^stats", views.OperatorStatsAPIView.as_view(),
                    name='operator-stats'),
            ])),
    re_path(r"^tablo/", views.TabloAPIView.as_view()),
    re_path(r"^registrator/talon/cancel",
            views.RegistratorTalonActionAPIView().as_view())
]
