from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import views
from dataaccess.views import DataAccessAPIView

# The api.gdex.ucar.edu subdomain (apis/urls.py) also serves apis/citations/urls.py

_urlpatterns = [
    # Tags and endpoints are displayed in the order they are declared here

    # "ARCO" tag
    path(r'arco_vars/<dsid>/', views.get_arco_variables),
    path(r'has_arco/<dsid>/', views.has_arco),
    path(r'search_arco_vars/<dsid>/<search_text>', views.search_arco_variables),

    # "requests" tag
    path(r'control_file_template/<dsid>/', views.get_control_file_template),
    path(r'control_file_template_old/<dsid>/', views.get_control_file_template_old ),
    path(r'get_req_files/<rindex>/', views.get_req_files ),
    path(r'get_req_files_old/<rindex>/', views.get_req_files_old ),
    path(r'get_status/', views.get_status ),
    path(r'get_status/<rindex>/', views.get_status ),
    path(r'metadata/<dsid>/', views.get_metadata ),
    path('paramsummary/<dsid>/', views.param_summary, name='paramsummary'),
    path(r'purge/<rindex>/', views.purge ),
    path(r'status/', views.get_status ),
    path(r'status/<rindex>/', views.get_status ),
    path(r'submit/', views.submit ),
    path(r'submit_json/', views.submit ),
    path(r'summary/<dsid>/', views.get_summary ),

    # "Dataset-level Metadata" tag
    path(r'datasets/', views.get_all_datasets ),
    path(r'datasets/<dsid>/abstract/', views.get_abstract),
    path(r'datasets/<dsid>/acknowledgment/', views.get_acknowledgement ),
    path(r'datasets/<dsid>/contributors/', views.get_contributors ),
    path(r'datasets/<dsid>/data_formats/', views.get_data_formats ),
    path(r'datasets/<dsid>/data_license/', views.get_data_license ),
    path(r'datasets/<dsid>/data_types/', views.get_data_types ),
    path(r'datasets/<dsid>/documentation/', views.get_dataset_documentation ),
    path(r'datasets/<dsid>/publications/', views.get_publications ),
    path(r'datasets/<dsid>/related_datasets/', views.get_related_datasets ),
    path(r'datasets/<dsid>/resources/', views.get_related_resources ),
    path(r'datasets/<dsid>/software/', views.get_dataset_software ),
    path(r'datasets/<dsid>/spatial_coverage/', views.get_spatial_coverage ),
    path(r'datasets/<dsid>/temporal/', views.get_temporal ),
    path(r'datasets/<dsid>/variables/', views.get_variables ),
    path(r'datasets/<dsid>/volume/', views.get_total_volume ),

    # "datasets" tag
    path(r'get_datasets/', views.get_datasets),
    path(r'datasets/<dsid>/data_access/root', DataAccessAPIView.as_view(), name='data-access-api' ),

    # "Files" tag
    path(r'datasets/<dsid>/filelist/', views.get_assembled_groups ),
    path(r'datasets/<dsid>/filelist/<gindex>/', views.get_assembled_groups ),
    path(r'datasets/<dsid>/filesearch/datatypes/', views.filesearch_datatypes),
    path(r'datasets/<dsid>/filesearch/filters/cyclone_fix/', views.filesearch_filters_cyclone_fix),
    path(r'datasets/<dsid>/filesearch/filters/grid/', views.filesearch_filters_grid),
    path(r'datasets/<dsid>/filesearch/filters/sensor/', views.filesearch_filters_sensor),
    path(r'datasets/<dsid>/filesearch/files/grid/', views.filesearch_files_grid),
    path(r'datasets/<dsid>/groups/', views.get_root_groups ),
    path(r'datasets/<dsid>/groups/<gindex>/', views.get_child_groups ),
    path(r'datasets/<dsid>/webfiles/<gindex>/', views.get_web_files ),
    path(r'datasets/<dsid>/webfiles/<gindex>/<filter_wfile>/', views.get_web_files ),

    # "staff" tag
    path(r'get_staff/', views.get_staff),
    path(r'get_staff/<dsid>/', views.get_staff_dsid),

    # "globus" tag
    path(r'globus_download/<rindex>/<endpoint>', views.globus_download ),

    # "metrics" tag
    path(r'metrics/ai_datasets/', views.ai_datasets),
    path(r'metrics/gdex_volume/', views.gdex_volume),
    path(r'metrics/dataset/<dsid>/users_month/', views.dataset_users_month),
    path(r'metrics/dataset/<dsid>/users_year/', views.dataset_users_year),
    path(r'metrics/dataset/<dsid>/volume_month/', views.dataset_volume_month),
    path(r'metrics/dataset/<dsid>/volume_year/', views.dataset_volume_year),
    path(r'metrics/top_datasets/', views.top_datasets),
    path(r'metrics/total_datasets/', views.total_datasets),
    path(r'metrics/total_citations/', views.total_citations),
    path(r'metrics/total_requests/', views.total_requests),
    path(r'metrics/unique_users/', views.unique_users),
    path(r'metrics/volume_downloaded/', views.volume_downloaded),

    # Notebook script
    path(r'generate_notebook', views.generate_notebook),

    # Jira Webhook 
    path(r'jira-event/<ticket_id>', views.JiraEventReceiver.as_view(), name = 'jira-event-receiver'),

    path(r'clear_cache/<dsid>/', views.clear_cache),

    #path(r'accept/', views.accept),
    #path(r'reject/', views.reject)
]

urlpatterns = _urlpatterns + [
    path('schema/', SpectacularAPIView.as_view(patterns=[path('api/', include((_urlpatterns, 'api')))]), name='schema'),
    path('documentation/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
