from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^(?P<subpath>.*)$', views.filelist, name='exchange_filelist'),
]
