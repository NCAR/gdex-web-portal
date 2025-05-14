import sys
from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def metrics(request):
    return render(request,'metrics.html', {'display':True})

def realtime(request):
    return render(request,'realtime_metrics.html', {'display':True})

def requests(request):
    return render(request,'requests_metrics.html', {'display':True})
