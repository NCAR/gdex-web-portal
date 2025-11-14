
from django.shortcuts import render


# Create your views here.

def submit_data(request):
    return render(request,'submit.html', {'display':True})