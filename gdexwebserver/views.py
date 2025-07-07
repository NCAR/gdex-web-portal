from django.http import (
        HttpResponseBadRequest,
        HttpResponseForbidden,
        HttpResponseNotFound,
        HttpResponseServerError,
)
from django.shortcuts import render
import smtplib
from email.message import EmailMessage


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
        msg['To'] = "rdahelp@ucar.edu"
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
        return HttpResponseBadRequest("Bad request.")

    if request.POST['code'] == "403":
        return HttpResponseForbidden(
                "You are not authorized to access this information.")
    elif request.POST['code'] == "404":
        if 'url' in request.POST:
            return HttpResponseNotFound((
                    "The URL that you requested - <span class="
                    "\"bold underline\">{}</span> - does not exist.")
                    .format(request.POST['url']))
        else:
            return HttpResponseBadRequest("Bad request.")

    elif request.POST['code'] == "500":
        return HttpResponseServerError(
                "A server error occurred. Please try again later.")

    return HttpResponseBadRequest("Bad request.")
