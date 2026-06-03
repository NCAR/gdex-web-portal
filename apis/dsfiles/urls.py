from django.urls import path, re_path

from . import views


urlpatterns = [
    path('', views.swagger),
    re_path(r'^(?P<dsid>d[0-9]{6})/(?P<operation>datatypes)/$', views.respond_to_request),
    path('<dsid>/<operation>/<datatype>/', views.respond_to_request),
]
