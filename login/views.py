from django.shortcuts import render
from django.http import HttpResponse
import psycopg2
from django.conf import settings

from login.models import LoginPage

db_config = settings.RDADB['dssdb_config_pg']

# Create your views here.

def activated(request):
    if not 'action' in request.GET:
        return render(request, "404.html")

    if request.GET['action'] == "showerror" and not 'error' in request.GET:
        return render(request, "404.html")

    return render(request, "login/activated.html")

def expire_cookies(response, domain):
    response.delete_cookie('duser', domain=domain)
    response.delete_cookie('altID', domain=domain)
    response.delete_cookie('alttype', domain=domain)
    response.delete_cookie('auser', domain=domain)
    response.delete_cookie('dpass', domain=domain)
    response.delete_cookie('iuser', domain=domain)
    response.delete_cookie('twikiname', domain=domain)
    response.delete_cookie('session', domain=domain)

def password(request):
    ctx = {}
    if 'resetpass' in request.GET:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("select email from dssdb.ruser_passwd where reset_code = '" + request.GET['resetpass'] + "'")
        row = cursor.fetchone()
        cursor.close()
        if row != None:
            ctx.update({'email': row[0]})
        else:
            ctx.update({'email': False})

    return render(request, 'login/new_password.html', ctx)

def privacy_agreement(request):
    if 'tmp' in request.COOKIES:
        remember = ''
        if 'remember' in request.GET:
            remember = request.GET['remember']
        return_url = "" 
        if 'url' in request.GET:
            return_url = request.GET['url']
        response = render(request, 'login/privacy_agreement.html', {'duser': request.COOKIES['tmp'], 'remember': remember, 'return_url': return_url})
        response.delete_cookie('tmp', domain=request.META['SERVER_NAME'])
    else:
        response = render(request, 'login/login_page.html')
    return response

def register(request):
    return render(request, "404.html")
    ctx = {}
    ctx.update({'page':  LoginPage.objects.all()[0]})
    if 'error' in request.GET:
        ctx.update({'error': request.GET['error']})
    else:
        ctx.update({'error': False})

    return render(request, 'login/register.html', ctx)

def signout(request):
    request.COOKIES.pop('duser', None)
    request.COOKIES.pop('altID', None)
    request.COOKIES.pop('alttype', None)
    request.COOKIES.pop('auser', None)
    request.COOKIES.pop('dpass', None)
    request.COOKIES.pop('iuser', None)
    request.COOKIES.pop('twikiname', None)
    request.COOKIES.pop('sess', None)
    response = render(request, 'login/signed_out.html')
    expire_cookies(response, request.META['SERVER_NAME'])
    return response

def signin(request):
    return render(request, "404.html")
    if 'duser' in request.COOKIES:
        return render(request, "login/signed_in.html")
    else:
        ctx = {}
        if 'error' in request.GET:
            ctx.update({'error': request.GET['error']})
        else:
            ctx.update({'error': False})

        return render(request, "login/login_page.html", ctx)
