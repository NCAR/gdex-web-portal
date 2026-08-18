import logging
import psycopg2
import smtplib

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from email.message import EmailMessage

from . import utils

logger = logging.getLogger(__name__)


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


def server_error(request):
    """
    Custom 500 handler (registered as `handler500` in urls.py).

    Renders the branded 500.html, which extends base.html and so pulls in
    the normal site header/footer via wagtailmenus. Those menus hit the
    database, and a 500 is sometimes caused by the database being the
    problem in the first place -- so if rendering the branded page itself
    raises, fall back to a bare-bones response rather than letting the
    error handler's own exception take down the response entirely.
    """
    try:
        return render(request, "500.html", status=500)
    except Exception:
        logger.exception("Failed to render branded 500 page")
        return HttpResponse(
            "<h1>Something went wrong</h1>"
            "<h2>Sorry, an unexpected error occurred. Please try again "
            "soon.</h2>"
            "<p>If the problem persists, please contact the NSF NCAR "
            "Research Data Help desk at "
            "<a href=\"mailto:datahelp@ucar.edu\">datahelp@ucar.edu</a> "
            "for assistance.</p>",
            status=500,
        )


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
