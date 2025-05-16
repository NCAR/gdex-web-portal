from django.shortcuts import redirect
from django.urls import include, path, re_path

from . import views
from . import utils


urlpatterns = [
    re_path(r"^(d[0-9]{6})/$", views.description),
    re_path(r"^(d[0-9]{6})/bookmark/$", utils.bookmark),
    re_path(r"^(d[0-9]{6})/citation/", include("dataset_citation.urls")),
    re_path(r"^(d[0-9]{6})/dataaccess/$", views.build_matrix),
    re_path(r"^(d[0-9]{6})/documentation/$", views.get_documentation_table),
    re_path(r"^(d[0-9]{6})/listopt/([^/]+)/$", views.listopt),
    re_path(r"^(d[0-9]{6})/listopt/([^/]+)/([0-9]{1,})/", views.listopt_gindex),
    re_path(r"^(d[0-9]{6})/software/$", views.get_software_table),
    re_path(r"^(d[0-9]{6})/filelist/$", views.get_filelist_table),
    re_path(r"^(d[0-9]{6})/filelist/(.*)/$", views.get_filelist_table),
    re_path(r"^(d[0-9]{6})/detailed_metadata/$", views.get_detailed_metadata),
    re_path(r"^(d[0-9]{6})/metadata_view/$", views.metadata_view),
    re_path(r"^(d[0-9]{6})/metrics/$", views.get_metrics),
    re_path(r"^(d[0-9]{6})/facbrowse/", include("facbrowse.urls")),
    re_path(r"^(d[0-9]{6})/provenance/", include("dataset_provenance.urls")),
    re_path(r"^request/(?P<rqstid>\w+[0-9]+)/$", views.get_request),
    re_path(r"^ds([0-9]{3})[\-\.]([0-9])/(.{0,})$",
        lambda request, id1, id2, rest:
            redirect(f"/datasets/d{id1}00{id2}/{rest}", permanent=True)
    ),
]
