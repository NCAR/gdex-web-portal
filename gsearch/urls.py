from django.urls import path, include
from globus_portal_framework.urls import register_custom_index
from . import views

register_custom_index('dssearch', ['dataset-search'])

urlpatterns = [
    path('ai-ready/', views.ai_ready_datasets, name='ai_ready_datasets'),
    path('popular/', views.popular_datasets, name='popular_datasets'),
    # Override the default Globus portal framework search view with the custom gsearch view
    path('<dssearch:index>/', views.dataset_search, name='search'),
    # Globus portal framework URLs
    path('', include('globus_portal_framework.urls')),
    path('', include('social_django.urls', namespace='social')),
]
