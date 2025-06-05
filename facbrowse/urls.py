from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"(.{1,})/customize/", views.do_customize),
    re_path(r"(.{1,})/query/(.{1,})/", views.do_query),
]
