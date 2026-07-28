from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from ..forms import ACCESS_METHOD_CHOICES
from ..models import SUBMISSION_TYPE_CHOICES, Submission
from .common import (
    PORTAL_VIEW_MODE_SESSION_KEY,
    _agent_view_active,
    _format_dataset_size,
    _get_owned_submission,
    _portal_dev_mode,
    portal_view,
)


@portal_view
def data_submission_portal_set_view_mode(request):
    """Flips the superuser-only agent/customer sidebar toggle. Anyone else
    posting here is a no-op -- they always see their own submissions
    regardless of the session value."""
    if request.method == 'POST' and request.user.is_superuser:
        view_mode = 'customer' if request.POST.get('view_mode') == 'customer' else 'agent'
        request.session[PORTAL_VIEW_MODE_SESSION_KEY] = view_mode

    next_url = request.POST.get('next')
    if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = reverse('data-submission-portal')
    return redirect(next_url)


@portal_view
def data_submission_portal(request):
    show_all = _portal_dev_mode() or _agent_view_active(request)
    datasets = Submission.objects.all() if show_all else Submission.objects.filter(submitted_by=request.user)
    datasets = datasets.order_by('-created')

    query = request.GET.get('q', '').strip()
    if query:
        datasets = datasets.filter(dataset_title__icontains=query)

    submission_type = request.GET.get('type', '')
    if submission_type in dict(SUBMISSION_TYPE_CHOICES):
        datasets = datasets.filter(submission_type=submission_type)

    return render(request, 'datasubmit/submission_portal/my_datasets/home.html', {
        'datasets': datasets,
        'query': query,
        'submission_type': submission_type,
        'submission_type_choices': SUBMISSION_TYPE_CHOICES,
    })

@portal_view
def data_submission_portal_view(request, pk):
    dataset = _get_owned_submission(request, pk, prefetch=('locations',))

    access_method_labels = dict(ACCESS_METHOD_CHOICES)
    locations = [
        {
            'location': loc.location,
            'access_method_label': access_method_labels.get(loc.access_method, loc.access_method),
            'access_verification': loc.access_verification,
        }
        for loc in dataset.locations.all()
    ]

    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-overview.html', {
        'dataset': dataset,
        'dataset_size_display': _format_dataset_size(dataset.dataset_size_mb),
        'locations': locations,
        'active_tab': 'Home',
    })

@portal_view
def data_submission_portal_files(request, pk):
    dataset = _get_owned_submission(request, pk, prefetch=('locations',))

    access_method_labels = dict(ACCESS_METHOD_CHOICES)
    locations = [
        {
            'location': loc.location,
            'access_method_label': access_method_labels.get(loc.access_method, loc.access_method),
            'access_verification': loc.access_verification,
        }
        for loc in dataset.locations.all()
    ]

    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-files.html', {
        'dataset': dataset,
        'locations': locations,
        'active_tab': 'Files',
    })

@portal_view
def data_submission_portal_metadata(request, pk):
    dataset = _get_owned_submission(request, pk)
    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-metadata.html', {
        'dataset': dataset,
        'active_tab': 'Metadata',
    })
