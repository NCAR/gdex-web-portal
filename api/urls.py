from django.urls import path
from . import views
from dataaccess.views import DataAccessAPIView

urlpatterns = [
    path('paramsummary/<dsid>/', views.param_summary, name='paramsummary'),
    path(r'get_staff/', views.get_staff),
    path(r'get_datasets/', views.get_datasets),
    path(r'metadata/<dsid>/', views.get_metadata ),
    path(r'summary/<dsid>/', views.get_summary ),
    path(r'submit/', views.submit ),
    path(r'submit_json/', views.submit ),
    path(r'print_help/', views.print_help ),
    path(r'help/', views.print_help ),
    path(r'control_file_template/<dsid>/', views.get_control_file_template),
    path(r'control_file_template_old/<dsid>/', views.get_control_file_template_old ),
    path(r'status/<rindex>/', views.get_status ),
    path(r'status/', views.get_status ),
    path(r'get_status/<rindex>/', views.get_status ),
    path(r'get_status/', views.get_status ),
    path(r'get_req_files/<rindex>/', views.get_req_files ),
    path(r'get_req_files_old/<rindex>/', views.get_req_files_old ),
    path(r'globus_download/<rindex>/<endpoint>', views.globus_download ),
    path(r'purge/<rindex>/', views.purge ),

    # Metrics
    path(r'metrics/volume_downloaded/', views.volume_downloaded ),
    path(r'metrics/unique_users/', views.unique_users ),

    # Notebook script
    path(r'generate_notebook', views.generate_notebook),

    # Dataset calls
    path(r'datasets/<dsid>/documentation/', views.get_dataset_documentation ),
    path(r'datasets/<dsid>/software/', views.get_dataset_software ),
    path(r'datasets/<dsid>/groups/', views.get_root_groups ),
    path(r'datasets/<dsid>/groups/<gindex>/', views.get_child_groups ),
    path(r'datasets/<dsid>/webfiles/<gindex>/', views.get_web_files ),
    path(r'datasets/<dsid>/webfiles/<gindex>/<filter_wfile>/', views.get_web_files ),
    path(r'datasets/<dsid>/filelist/<gindex>/', views.get_assembled_groups ),
    path(r'datasets/<dsid>/filelist/', views.get_assembled_groups ),
    path(r'datasets/<dsid>/abstract/', views.get_abstract),
    path(r'datasets/<dsid>/acknowledgment/', views.get_acknowledgement ),
    path(r'datasets/<dsid>/temporal/', views.get_temporal ),
    path(r'datasets/<dsid>/variables/', views.get_variables ),
    path(r'datasets/<dsid>/publications/', views.get_publications ),
    path(r'datasets/<dsid>/data_license/', views.get_data_license ),
    path(r'datasets/<dsid>/data_types/', views.get_data_types ),
    path(r'datasets/<dsid>/data_formats/', views.get_data_formats ),
    path(r'datasets/<dsid>/spatial_coverage/', views.get_spatial_coverage ),
    path(r'datasets/<dsid>/contributors/', views.get_contributors ),
    path(r'datasets/<dsid>/volume/', views.get_total_volume ),
    path(r'datasets/<dsid>/resources/', views.get_related_resources ),
    path(r'datasets/<dsid>/related_datasets/', views.get_related_datasets ),
    path(r'datasets/', views.get_all_datasets ),
    path(r'datasets/<dsid>/data_access/root', DataAccessAPIView.as_view(), name='data-access-api' )


    #path(r'accept/', views.accept),
    #path(r'reject/', views.reject)
]
