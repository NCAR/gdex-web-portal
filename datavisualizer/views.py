from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
import requests
import json

def fetch_json_from_url(url):
    """
    Fetch JSON data from a URL and convert it to a Python dictionary
    Args:
        url (str): The URL containing JSON data
    Returns:
        dict: The JSON data as a Python dictionary
    """
    try:
        # Send GET request to the URL
        response = requests.get(url)
        # Raise an exception for bad status codes
        response.raise_for_status()
        # Parse JSON response directly 
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from URL: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e}")
        return None

def get_all_caches(result):
    """
    Extracts all cache locations, separating healthy and unhealthy caches.
    Args:
        result (list): List of dictionaries containing cache server data.
    Returns:
        dict: Dictionary with 'down_caches' and 'healthy_caches' lists.
    Raises:
        ValueError: If the result is empty or None.
    """
    if not result:
        raise ValueError("Result is empty or None")

    down_caches = []
    healthy_caches = []

    for data in result:
        # Check if the data is a cache or NCAR server
        if data.get('type') == 'Cache' or "NCAR" in data.get('name'):
            lat = data.get('latitude')
            lon = data.get('longitude')

            # Skip if both latitude and longitude are 0
            if lat == 0 and lon == 0:
                continue

            cache_info = {
                'name': data.get('name'),
                'type': data.get('type'),
                'status': data.get('healthStatus'),
                'latitude': lat,
                'longitude': lon
            }

            # Check if the health status is not OK
            if data.get('healthStatus') != 'OK' and data.get('healthStatus') != 'Health Test Disabled':
                down_caches.append(cache_info)
            elif data.get('type') == 'Cache' and data.get('healthStatus') == "OK":
                healthy_caches.append(cache_info)

    return {
        'down_caches': down_caches,
        'healthy_caches': healthy_caches
    }

def get_cache_data():
    """
    Helper function to get cache data 
    Returns:
        dict: Dictionary with 'down_caches' and 'healthy_caches' lists
    """
    url = "https://osdf-director.osg-htc.org/api/v1.0/director_ui/servers"
    result = fetch_json_from_url(url)
    down_caches = []
    healthy_caches = []
    
    if result:
        try:
            cache_data = get_all_caches(result)
            down_caches = cache_data['down_caches']
            healthy_caches = cache_data['healthy_caches']
        except ValueError as e:
            print(f"Error getting cache data: {e}")
    else:
        print("No data received from API")
    
    return {'down_caches': down_caches, 'healthy_caches': healthy_caches}

# Updated Index view with cache data
class Index(TemplateView):
    template_name = 'datavisualizer/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cache_data = get_cache_data()
        context['down_caches'] = cache_data['down_caches']
        context['healthy_caches'] = cache_data['healthy_caches']
        
        return context

def get_cache_data_api(request):
    """
    API endpoint to get cache data as JSON 
    """
    cache_data = get_cache_data()
    return JsonResponse(cache_data)