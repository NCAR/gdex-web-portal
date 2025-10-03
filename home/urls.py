from django.urls import path
from . import views

urlpatterns = [
    path('', views.metrics),
    path('realtime/', views.realtime),
    path('requests/', views.requests),
    path('by-the-numbers/', views.by_the_numbers),
]
