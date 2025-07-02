from django.urls import path

from . import aggregations
from . import bookmarks
from . import dsrqsts
from . import views


urlpatterns = [
    path("", views.dashboard),
    path("aggregations/count/", aggregations.get_count),
    path("aggregations/", aggregations.get_aggregations),
    path("bookmarks/count/", bookmarks.get_count),
    path("bookmarks/<dsid>/", bookmarks.do_delete),
    path("bookmarks/", bookmarks.get_bookmarks),
    path("requests/count/", dsrqsts.get_count),
    path("requests/extend/", dsrqsts.extend),
    path("requests/", dsrqsts.get_dsrqsts),
    path("version/", views.get_version),
]
