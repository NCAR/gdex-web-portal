from django.urls import path, re_path
from . import views


urlpatterns = [
    path("", views.metaman_page),
    path("manage-datasets/add/", views.add),
    path("manage-datasets/cancel/<dsid>/", views.cancel),
    path("manage-datasets/change-history/<dsid>/", views.change_history),
    path("manage-datasets/choose-existing-dataset/",
         views.choose_existing_dataset),
    path("manage-datasets/cite-contributors/", views.cite_contributors),
    path("manage-datasets/commit-changes/<dsid>/", views.commit_changes),
    path("manage-datasets/commit-field/<fieldname>/", views.commit_field),
    path("manage-datasets/create/<dsid>/", views.create),
    path("manage-datasets/delete/<dsid>/", views.delete),
    path("manage-datasets/discard-changes/<dsid>/", views.discard_changes),
    path("manage-datasets/edit/<dsid>/", views.edit),
    re_path(r"manage-datasets/edit\_(.*)/", views.edit_item),
    re_path(r"manage-datasets/get\_(.*)/", views.get_item),
    path("manage-datasets/help/<help_type>/", views.ds_help),
    path("manage-datasets/metadata-summary/<dsid>/", views.metadata_summary),
    path("manage-datasets/remove/", views.remove),
    path("manage-datasets/reorder-authors/", views.reorder_authors),
    path("manage-datasets/show-logos/", views.show_logos),
    path("manage-datasets/show-words/", views.show_words),
    path("manage-datasets/upload-logo/", views.upload_logo),
    path("manage-datasets/web-file-access/<dsid>/", views.web_access),
    re_path("manage-datasets/.*/$", views.unknown),
    path("manage-dataset-dois/choose-existing-dataset/",
         views.choose_existing_dataset),
    path("manage-dataset-dois/create/<dsid>/", views.assign),
    path("manage-dataset-dois/supersede/<dsid>/", views.supersede),
    path("manage-dataset-dois/adopt/<dsid>/", views.adopt),
    path("spellcheck-request", views.spellcheck_request),
    path("usage-guide/<slug>/", views.usage_guide),
]
