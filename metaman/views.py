from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import render
from home.models import ManPage
from wagtail.models import Page

from . import datasets
from . import dois
from .get_items import render_map as MAP
from .models import MetamanPage
from . import utils


def metaman_page(request):
    if (settings.ICOOKIE['id'] not in request.COOKIES or
            settings.ICOOKIE['content'] not in
            request.COOKIES[settings.ICOOKIE['id']]):
        return render(request, "403.html")

    qs = Page.objects.type(MetamanPage)
    return render(request, "metaman/metaman_page.html",
                  qs[0].get_context(request))


def add(request):
    return datasets.add(request)


def cancel(request, dsid):
    return datasets.cancel(request, dsid)


def commit_field(request, fieldname):
    return datasets.commit_field(request, fieldname)


def create(request, dsid):
    return datasets.create(request, dsid)


def change_history(request, dsid):
    return datasets.change_history(request, dsid)


def choose_existing_dataset(request):
    return utils.choose_existing_dataset(request)


def cite_contributors(request):
    return utils.cite_contributors(request)


def commit_changes(request, dsid):
    return datasets.commit_changes(request, dsid)


def delete(request, dsid):
    return datasets.delete(request, dsid)


def discard_changes(request, dsid):
    return datasets.discard_changes(request, dsid)


def edit(request, dsid):
    return datasets.edit(request, dsid)


def edit_item(request, item):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if item in MAP and 'itemList' in request.POST:
        ctx = {'title': MAP[item]['edit-title'], 'item': item}
        items = request.POST['itemList'].split("\n")
        opts = []
        start = MAP[item]['item-start'] if 'item-start' in MAP[item] else 0
        for n in range(start, len(items)):
            if item == "reference":
                opts.append({'value': (items[n].replace("\"", "&amp;quot;") +
                                       "///" + str(n)),
                             'description': items[n]})
            else:
                opts.append({'value': items[n].replace("\"", "&amp;quot;"),
                             'description': items[n]})

        ctx.update({'options': opts})
        return render(request, "metaman/datasets/edit_item.html", ctx)

    return render(request, "metaman/datasets/edit_item.html",
                  {'error': ("Unknown item '" + item +
                             "' or missing item list")})


def get_item(request, item):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if item in MAP:
        return MAP[item]['getter'](request)

    return render(request, "404.html")


def ds_help(request, help_type):
    return datasets.help(request, help_type)


def metadata_summary(request, dsid):
    return utils.metadata_summary(request, dsid)


def reorder_authors(request):
    return utils.reorder_authors(request)


def remove(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if ('field' in request.POST and request.POST['field'] in MAP and 'items'
            in request.POST):
        items = utils.trim(request.POST['items']).split("\n")
        items = [{'value': item.replace("\"", "&amp;quot;"),
                  'description': item} for item in items]

        return render(request, "metaman/datasets/remove_item.html",
                      {'title': MAP[request.POST['field']]['remove-title'],
                       'items': items})

    return render(request, "404.html")


def show_logos(request):
    return utils.show_logos(request)


def show_words(request):
    return utils.show_words(request)


def upload_logo(request):
    return utils.upload_logo(request)


def web_access(request, dsid):
    return datasets.web_access(request, dsid)


def assign(request, dsid):
    return dois.assign(request, dsid)


def supersede(request, dsid):
    return dois.supersede(request, dsid)


def adopt(request, dsid):
    return dois.adopt(request, dsid)


def unknown(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    return render(request, "metaman/unknown.html")


def spellcheck_request(request):
    return utils.spellcheck_request(request)


def usage_guide(request, slug):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    qs = Page.objects.type(ManPage).filter(slug=slug)
    if len(qs) == 0:
        return render(request, "404.html")

    content = str(
        qs.first().specific.body
    ).replace(
        "&gt;", ">"
    ).replace(
        "&lt;", "<"
    ).replace(
        "&quot;", "\""
    ).replace(
        "{{ csrf_token }}", get_token(request)
    )
    return render(request, "metaman/usage_guide.html",
                  {'content': content})
