from django.urls import path
from . import views
    
urlpatterns = [
    path('authcallback/', views.authcallback, name='authcallback-view'),
    path('filelist/', views.save_filelist),
    path('browsecallback/', views.browsecallback, name='browsecallback-view'),
    path('transfer/', views.transfer, name='transfer-view'),
    path('submit-transfer/', views.submit_transfer, name='submit-transfer-view'),
    path('status/<uuid:task_id>', views.transfer_status, name='status-view'),
]
