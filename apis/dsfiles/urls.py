from django.urls import path

from . import views


urlpatterns = [
    path('', views.swagger),
    path('<dsid>/filters/', views.filters),
]
