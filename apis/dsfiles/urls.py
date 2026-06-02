from django.urls import path, re_path

from . import views


urlpatterns = [
    path('', views.swagger),
    re_path(r'^(?P<dsid>d[0-9]{6})/(?P<operation>([^/]*){1})/(?P<data_type>([^/]*){0,})$', views.respond_to_request),
]
