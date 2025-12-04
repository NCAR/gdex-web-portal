
from django.shortcuts import render


# Create your views here.

def submit_data(request):
    return render(request,'submit/submit.html', {'display':True})