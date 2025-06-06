import sys
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

# Create your views here.

def logout(request):
    return render(request,'logout.html', {'display':True})

def newtoken(request):
    token,valid_date = request.user.usertoken.generate_new_token()
    return JsonResponse({'token':str(token), 'valid_date':str(valid_date)})

    
