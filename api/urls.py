from django.urls import path
from . import views

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
    
    # Notebook script
    path(r'generate_notebook', views.generate_notebook),
    
    # dataset calls
    path(r'datasets/<dsid>/documentation/', views.get_dataset_documentation ),
    path(r'datasets/<dsid>/software/', views.get_dataset_software ),
    path(r'datasets/<dsid>/groups/', views.get_root_groups ),
    path(r'datasets/<dsid>/groups/<gindex>/', views.get_child_groups ),
    path(r'datasets/<dsid>/webfiles/<gindex>/', views.get_web_files ),
    path(r'datasets/<dsid>/webfiles/<gindex>/<filter_wfile>/', views.get_web_files ),
    path(r'datasets/<dsid>/filelist/<gindex>/', views.get_assembled_groups ),
    path(r'datasets/<dsid>/filelist/', views.get_assembled_groups ),

    #path(r'accept/', views.accept),
    #path(r'reject/', views.reject)
]
