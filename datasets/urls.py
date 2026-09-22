from django.shortcuts import redirect
from django.urls import include, path, re_path

from . import views
from . import utils

urlpatterns = [
    re_path(r"^(d[0-9]{6})/$", views.description, name="dataset_description"),
    re_path(r"^(d[0-9]{6})/bookmark/$", utils.bookmark, name="dataset_bookmark"),
    re_path(r"^(d[0-9]{6})/citation/", include("dataset_citation.urls")),
    re_path(r"^(d[0-9]{6})/dataaccess/$", views.build_matrix, name="dataset_dataaccess"),
    re_path(r"^(d[0-9]{6})/documentation/$", views.get_documentation_table, name="dataset_documentation"),
    re_path(r"^(d[0-9]{6})/listopt/([^/]+)/$", views.listopt, name="dataset_listopt"),
    re_path(r"^(d[0-9]{6})/listopt/([^/]+)/([0-9]{1,})/", views.listopt_gindex, name="dataset_listopt_gindex"),
    re_path(r"^(d[0-9]{6})/software/$", views.get_software_table, name="dataset_software"),
    re_path(r"^(d[0-9]{6})/filelist/$", views.get_filelist_table, name="dataset_filelist"),
    re_path(r"^(d[0-9]{6})/filelist/(.*)/$", views.get_filelist_table, name="dataset_filelist_filtered"),
    re_path(r"^(d[0-9]{6})/detailed_metadata/$", views.get_detailed_metadata, name="dataset_detailed_metadata"),
    re_path(r"^(d[0-9]{6})/metadata_view/$", views.metadata_view, name="dataset_metadata_view"),
    re_path(r"^(d[0-9]{6})/metadata_view/(\w+ML)/(.*)$", views.markup_view, name="dataset_markup_view"),
    re_path(r"^(d[0-9]{6})/metadata_product_detail/(\w+ML)/([0-9]+)/([0-9]+)/(.*)$", views.product_detail, name="dataset_product_detail"),
    re_path(r"^(d[0-9]{6})/metrics/$", views.get_metrics, name="dataset_metrics"),
    re_path(r"^(d[0-9]{6})/example/$", views.example_view, name="dataset_example"),
    re_path(r"^(d[0-9]{6})/facbrowse/", include("facbrowse.urls")),
    re_path(r"^(d[0-9]{6})/provenance/", include("dataset_provenance.urls")),
    re_path(r"^(d[0-9]{6})/native/", views.get_native, name="dataset_native"),
    re_path(r"^request/(?P<rqstid>\w+[0-9]+)/$", views.get_request, name="dataset_get_request"),
    re_path(r"^(d[0-9]{6})/request/", views.submit_web_data_request, name="submit_web_data_request"),
    re_path(r"^(d[0-9]{6})/custom-subset/", views.custom_subset, name="custom_subset"),
    re_path(r"^ds([0-9]{3})[\-\.]([0-9])/(.{0,})$",
        lambda request, id1, id2, rest:
            redirect(f"/datasets/d{id1}00{id2}/{rest}", permanent=True)
    ),
    path("collections/", views.collections, name="dataset_collections"),
]
