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

def test_home(request):
    return render(request, 'home/home-test.html', {'display': True})

def by_the_numbers(request):
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
    return render(request, 'home/splash.html', ctx)

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
