from django.urls import path

from . import views


urlpatterns = [
    path('', views.swagger),
    path('<dsid>/datatypes/', views.respond_to_request),
    path('<dsid>/<operation>/<datatype>/', views.respond_to_request),
]
