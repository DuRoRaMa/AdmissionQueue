from django.urls import re_path, path

from . import views

app_name = 'helper'
urlpatterns = [
    re_path(r"^list", views.HelperListAPIView.as_view()),
    re_path(r"^request", views.HelpRequestCreateAPIView.as_view()),
]
