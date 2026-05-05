import psycopg2
import smtplib

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from email.message import EmailMessage

from . import utils


def contact_us(request):
    ctx = {}
    if 'd' in request.GET:
        ctx.update({'dsnum': request.GET['d']})

    if 's' in request.GET:
        ctx.update({'subject': request.GET['s']})

    if 'u' in request.GET:
        ctx.update({'return_url': request.GET['u']})

    if request.method == "POST":
        msg = EmailMessage()
        msg['From'] = request.POST['email']
        msg['To'] = "datahelp@ucar.edu"
        msg['Subject'] = request.POST['subject']
        msg.set_content(request.POST['request'])
        with smtplib.SMTP("localhost") as s:
            s.send_message(msg)

        ctx.update({'submitted': True})
        if 'modal' in request.POST:
            ctx.update({'show_modal_close': True})

    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "contact_us.html"
        ctx.update({'from_modal_window': True})
    else:
        template = "unity/contact_us_page.html"

    return render(request, template, ctx)


def error(request):
    if 'code' not in request.POST:
        return HttpResponse("Bad request.")

    if request.POST['code'] == "403":
        return HttpResponse(
                "You are not authorized to access this information.")
    elif request.POST['code'] == "404":
        if 'url' in request.POST:
            return HttpResponse((
                    "The URL that you requested - <span class="
                    "\"bold underline\">{}</span> - does not exist.")
                    .format(request.POST['url']))
        else:
            return HttpResponse("Bad request.")

    elif request.POST['code'] == "500":
        return HttpResponse(
                "A server error occurred. Please try again later.")

    return HttpResponse("Bad request.")


@csrf_exempt
def unlink(request):
    return utils.unlink(request)


@csrf_exempt
def upload(request):
    return utils.upload(request)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "Disallow: /metaman/",
        "Disallow: /redeploy/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def do_redirect(request, old_gdex_path):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select dsid from search.gdex_crossref where old_gdex_path = "
                "%s"), (old_gdex_path, ))
        dsid = cursor.fetchone()
        if dsid is None:
            return render(request, "404.html", status=404)

        return redirect("/datasets/" + dsid[0] + "/")
    except Exception:
        return render(request, "500.html", status=500)
