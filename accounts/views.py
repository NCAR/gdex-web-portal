import sys
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from accounts.adapters import MyAccountAdapter

# Create your views here.

def logout(request):
    response = render(request, 'logout.html', {'display': True})
    # allauth's own adapter.logout() runs before any response exists, so the
    # legacy identity cookies are cleared here instead, on the fixed
    # post-logout redirect target (ACCOUNT_LOGOUT_REDIRECT_URL).
    MyAccountAdapter().remove_cookies(response)
    return response

def signup(request):
    # Email/password signup is closed (see MyAccountAdapter), so signup is
    # ORCID-only; this replaces allauth's account_signup view.
    return render(request, 'account/signup.html')

def newtoken(request):
    token,valid_date = request.user.usertoken.generate_new_token()
    return JsonResponse({'token':str(token), 'valid_date':str(valid_date)})

    
