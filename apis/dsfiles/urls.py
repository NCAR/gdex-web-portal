from django.urls import path

from . import views


urlpatterns = [
    path('', views.swagger),
    path('<dsid>/<operation>/', views.respond_to_request),
]
