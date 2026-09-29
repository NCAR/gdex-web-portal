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
    path(r'clear_cache/<dsid>/', views.clear_cache),

    # Metrics
    path(r'metrics/volume_downloaded/', views.volume_downloaded, name='volume_downloaded'),
    path(r'metrics/unique_users/', views.unique_users, name='unique_users'),
    path(r'metrics/total_datasets/', views.total_datasets, name='total_datasets'),
    path(r'metrics/total_citations/', views.total_citations, name='total_citations'),
    path(r'metrics/gdex_volume/', views.gdex_volume, name='gdex_volume'),
    path(r'metrics/total_requests/', views.total_requests, name='total_requests'),
    path(r'metrics/top_datasets/', views.top_datasets, name='top_datasets'),
    path(r'metrics/ai_datasets/', views.ai_datasets, name='ai_datasets'),
    path(r'metrics/dataset/<dsid>/users_month/', views.dataset_users_month, name='dataset_users_month'),
    path(r'metrics/dataset/<dsid>/users_year/', views.dataset_users_year, name='dataset_users_year'),
    path(r'metrics/dataset/<dsid>/volume_month/', views.dataset_volume_month, name='dataset_volume_month'),
    path(r'metrics/dataset/<dsid>/volume_year/', views.dataset_volume_year, name='dataset_volume_year'),

    # Notebook script
    path(r'generate_notebook', views.generate_notebook),

    # Jira Webhook 
    path(r'jira-event/<ticket_id>', views.JiraEventReceiver.as_view(), name = 'jira-event-receiver'),

    # "Dataset-level Metadata" tag
    path(r'datasets/', views.get_all_datasets, name='get-all-datasets'),
    path(r'datasets/<dsid>/abstract/', views.get_abstract, name='get-abstract'),
    path(r'datasets/<dsid>/acknowledgment/', views.get_acknowledgement, name='get-acknowledgement'),
    path(r'datasets/<dsid>/contributors/', views.get_contributors, name='get-contributors'),
    path(r'datasets/<dsid>/data_formats/', views.get_data_formats, name='get-data-formats'),
    path(r'datasets/<dsid>/data_license/', views.get_data_license, name='get-data-license'),
    path(r'datasets/<dsid>/data_types/', views.get_data_types, name='get-data-types'),
    path(r'datasets/<dsid>/documentation/', views.get_dataset_documentation, name='get-dataset-documentation'),
    path(r'datasets/<dsid>/publications/', views.get_publications, name='get-publications'),
    path(r'datasets/<dsid>/related_datasets/', views.get_related_datasets, name='get-related-datasets'),
    path(r'datasets/<dsid>/resources/', views.get_related_resources, name='get-related-resources'),
    path(r'datasets/<dsid>/software/', views.get_dataset_software, name='get-dataset-software'),
    path(r'datasets/<dsid>/spatial_coverage/', views.get_spatial_coverage, name='get-spatial-coverage'),
    path(r'datasets/<dsid>/temporal/', views.get_temporal, name='get-temporal'),
    path(r'datasets/<dsid>/variables/', views.get_variables, name='get-variables'),
    path(r'datasets/<dsid>/volume/', views.get_total_volume, name='get-total-volume'),

    # "datasets" tag
    path(r'get_datasets/', views.get_datasets, name='get-datasets'),
    path(r'datasets/<dsid>/data_access/root', DataAccessAPIView.as_view(), name='data-access-api'),

    # "Files" tag
    path(r'datasets/<dsid>/filelist/', views.get_assembled_groups, name='get-assembled-groups'),
    path(r'datasets/<dsid>/filelist/<gindex>/', views.get_assembled_groups, name='get-assembled-groups-gindex'),
    path(r'datasets/<dsid>/filesearch/datatypes/', views.filesearch_datatypes, name='filesearch-datatypes'),
    path(r'datasets/<dsid>/filesearch/filters/cyclone_fix/', views.filesearch_filters_cyclone_fix, name='filesearch-filters-cyclone-fix'),
    path(r'datasets/<dsid>/filesearch/filters/grid/', views.filesearch_filters_grid, name='filesearch-filters-grid'),
    path(r'datasets/<dsid>/filesearch/filters/sensor/', views.filesearch_filters_sensor, name='filesearch-filters-sensor'),
    path(r'datasets/<dsid>/filesearch/files/cyclone_fix/', views.filesearch_files_cyclone_fix, name='filesearch-files-cyclone-fix'),
    path(r'datasets/<dsid>/filesearch/files/grid/', views.filesearch_files_grid, name='filesearch-files-grid'),
    path(r'datasets/<dsid>/filesearch/files/sensor/', views.filesearch_files_sensor, name='filesearch-files-sensor'),
    path(r'datasets/<dsid>/filesearch/results/<result_id>/<int:page_num>/', views.filesearch_result_set, name='filesearch-result-set'),
    path(r'datasets/<dsid>/groups/', views.get_root_groups, name='get-root-groups'),
    path(r'datasets/<dsid>/groups/<gindex>/', views.get_child_groups, name='get-child-groups'),
    path(r'datasets/<dsid>/webfiles/<gindex>/', views.get_web_files, name='get-web-files'),
    path(r'datasets/<dsid>/webfiles/<gindex>/<filter_wfile>/', views.get_web_files, name='get-web-files-filtered'),

    # "staff" tag
    path(r'get_staff/', views.get_staff, name='get-staff'),
    path(r'get_staff/<dsid>/', views.get_staff_dsid, name='get-staff-dsid'),

    # "globus" tag
    path(r'globus_download/<rindex>/<endpoint>', views.globus_download),

    #path(r'accept/', views.accept),
    #path(r'reject/', views.reject)
]

urlpatterns = _urlpatterns + [
    path('schema/', SpectacularAPIView.as_view(patterns=[path('api/', include((_urlpatterns, 'api')))]), name='schema'),
    path('documentation/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
