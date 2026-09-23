from django.contrib import admin
from django.urls import path
from .views import Index, get_cache_data_api

urlpatterns = [
    path('', Index.as_view(), name='index'), 
    path('api/cache-data/', get_cache_data_api, name='cache_data_api'),
]