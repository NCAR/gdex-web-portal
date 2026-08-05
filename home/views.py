import sys
from django.shortcuts import render
from django.http import HttpResponse
from api import common
from api import views as api_views
import json
import requests as http_request
from datasets import utils

# Create your views here.

def metrics(request):
    return render(request,'metrics.html', {'display':True})

def realtime(request):
    return render(request,'realtime_metrics.html', {'display':True})

def requests(request):
    return render(request,'requests_metrics.html', {'display':True})

def by_the_numbers(request):
    return render(request, 'home/splash.html')

def test_splash(request):
    ctx = {
            'datasets': common.get_number_of_datasets(),
            'citations': common.get_total_citations(),
            'users' : common.get_number_of_unique_users(),
            'downloaded' : common.get_volume_downloaded(),
            'downloaded_db' : json.loads( # doing this to take advantage of cacheing
                        http_request.get(utils.get_hostname()+'/api/metrics/volume_downloaded/').content
                )['volume'],
            'volume' : common.get_gdex_volume(),
            'requests' : common.get_total_requests(),
            'top_datasets' : common.get_top_datasets(),
            'ai_datasets' : common.get_AI_datasets(),
    }
    return render(request, 'home/splash-test.html', ctx)

def ai_ready_datasets(request):
    try:
        raw = common.get_AI_datasets(limit=200)
        datasets = [{'dsid': row[0], 'title': row[1]} for row in raw]
    except Exception:
        datasets = []
    return render(request, 'home/ai-ready-datasets.html', {'datasets': datasets})

def popular_datasets(request):
    try:
        raw = common.get_top_datasets(top=50)
        if isinstance(raw, str):
            raw = []
        datasets = [
            {
                'dsid': ds.get('dataset', ''),
                'title': ds.get('OName', ''),
                'rank': ds.get('index', ''),
                'users': ds.get('Total Number of Unique Users', 'N/A'),
                'volume_tb': ds.get('Total Volume Downloaded (TB)', 'N/A'),
            }
            for ds in raw
        ]
    except Exception:
        datasets = []
    return render(request, 'home/popular-datasets.html', {'datasets': datasets})
