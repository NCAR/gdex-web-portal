from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start),
    path('refine/', views.refine),
    path('datasets/', views.show_datasets),
    path('compare/', views.compare),
]
