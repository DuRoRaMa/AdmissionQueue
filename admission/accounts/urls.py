# -*- coding: utf-8 -*-
from django.urls import re_path
 
from . import views
 
app_name = 'accounts'
urlpatterns = [
    re_path(r'^user/$', views.UserRetriaveAPIView.as_view())
]