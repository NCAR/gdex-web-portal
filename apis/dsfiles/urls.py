from django.urls import path

from . import views


urlpatterns = [
    path('', views.swagger),
    path('<dsid>/selections/', views.selections),
]
