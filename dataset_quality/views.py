from django.shortcuts import render

from datasets.utils import ng_gdex_id
from datasets.views import description

from .utils import build_checklist_context


def quality_checklist(request, dsid):
    dsid = ng_gdex_id(dsid)
    ctx = build_checklist_context(dsid)
    if ctx is None:
        return render(request, "404.html")

    if "HTTP_X_REQUESTED_WITH" in request.META:
        return render(request, "dataset_quality/quality_checklist.html", ctx)

    ctx["dsid"] = dsid
    return description(request, dsid,
                       template="dataset_quality/quality_checklist_page.html",
                       page_context=ctx)
