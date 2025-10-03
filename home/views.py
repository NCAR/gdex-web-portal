import sys
from django.shortcuts import render
from django.http import HttpResponse
from api import common

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
            'dowloaded' : common.get_volume_downloaded(),
            'volume' : common.get_gdex_volume()
    }
    return render(request, 'home/splash.html', ctx)
