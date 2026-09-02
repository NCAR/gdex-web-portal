from django.shortcuts import render

from .common import portal_view


@portal_view
def data_submission_portal_proposal_templates(request):
    return render(request, 'datasubmit/submission_portal/proposal_templates/home.html')
