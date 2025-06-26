from django.urls import path
from . import views

urlpatterns = [
    path('activated/', views.activated),
    path('password/', views.password),
    path('privacy/', views.privacy_agreement),
    path('register/', views.register),
    path('signout/', views.signout),
    path('signin/', views.signin),
]
