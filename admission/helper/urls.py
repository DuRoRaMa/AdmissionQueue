from django.urls import re_path, path

from . import views

app_name = 'helper'
urlpatterns = [
    re_path(r"^info", views.HelpInfoListAPIView.as_view()),
    re_path(r"^request", views.HelpRequestCreateAPIView.as_view()),
]
