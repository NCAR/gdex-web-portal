""" ICOADS API URL Configuration """
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.swagger),
    re_path(r'^[a-zA-Z0-9].*$', views.icoads),
]
