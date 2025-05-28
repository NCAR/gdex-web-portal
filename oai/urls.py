from django.urls import path
from . import views

urlpatterns = [
    path('', views.respond_to_request),
]
