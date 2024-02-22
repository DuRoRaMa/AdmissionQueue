# -*- coding: utf-8 -*-
from django.urls import re_path
 
from . import views
 
app_name = 'accounts'
urlpatterns = [
    re_path(r'^login/$', views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', views.LogoutView.as_view(), name= "logout")
]