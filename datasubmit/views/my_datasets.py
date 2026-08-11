from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from ..forms import ACCESS_METHOD_CHOICES, SUBMISSION_TYPE_CHOICES
from ..models import Submission, SubmissionStatus
from .common import (
    PORTAL_VIEW_MODE_SESSION_KEY,
    _agent_view_active,
    _current_status,
    _format_dataset_size,
    _get_owned_submission,
    _get_pre_submission,
    _owner_display,
    _portal_dev_mode,
    portal_view,
)

STATUS_META = {
    SubmissionStatus.Status.IN_PROGRESS: {'icon': 'fa-hourglass-half', 'color': 'warning'},
    SubmissionStatus.Status.PENDING_DECISION: {'icon': 'fa-triangle-exclamation', 'color': 'danger'},
    SubmissionStatus.Status.IN_REVIEW: {'icon': 'fa-magnifying-glass', 'color': 'primary'},
    SubmissionStatus.Status.PUBLISHED: {'icon': 'fa-circle-check', 'color': 'success'},
    SubmissionStatus.Status.CANCELED: {'icon': 'fa-ban', 'color': 'secondary'},
}
STATUS_ORDER = list(STATUS_META)

# Per-row progress bar. Pending Decision and Canceled aren't points along
# the pipeline -- they're excluded here (status_percent is None for them),
# so the template shows a plain badge/label instead of a bar for those rows.
STATUS_PROGRESS = {
    SubmissionStatus.Status.IN_PROGRESS: 50,
    SubmissionStatus.Status.IN_REVIEW: 75,
    SubmissionStatus.Status.PUBLISHED: 100,
}

# In Progress / Pending Decision / In Review share one card (each dataset
# shows its own status as a pill since the card itself spans all three);
# Published and Canceled stay in their own single-status cards.
ACTIVE_STATUSES = [SubmissionStatus.Status.IN_PROGRESS, SubmissionStatus.Status.PENDING_DECISION, SubmissionStatus.Status.IN_REVIEW]
CARD_DEFINITIONS = [
    {'key': 'active', 'label': 'Active', 'icon': 'fa-bolt', 'color': 'primary', 'statuses': ACTIVE_STATUSES},
    {'key': SubmissionStatus.Status.PUBLISHED, 'statuses': [SubmissionStatus.Status.PUBLISHED]},
    {'key': SubmissionStatus.Status.CANCELED, 'statuses': [SubmissionStatus.Status.CANCELED]},
]

# Tile label is deliberately shorter than the full SUBMISSION_TYPE_CHOICES
# sentence ("I am submitting my own dataset...") used by the wizard --
# that phrasing only makes sense as a question, not a stat-tile caption.
TYPE_META = {
    'own': {'icon': 'fa-database', 'color': 'success', 'tile_label': 'My Submissions'},
    'recommend': {'icon': 'fa-heart', 'color': 'info', 'tile_label': 'Wishlist Datasets'},
}

# Column headers become sort links keyed by these names; each maps to a
# callable that pulls the sort key off a dataset. Status sorts by its
# pipeline percent (matching the progress bar), not the label, since
# e.g. "canceled" < "in_progress" alphabetically isn't a meaningful order.
SORT_FIELDS = {
    'title': lambda d: (d.dataset_title or '').lower(),
    'status': lambda d: d.status_percent or 0,
    'created': lambda d: d.created,
}
# Widths here must stay in sync with the hardcoded column divs in each
# dataset row in home.html (Dataset/Submitted On/Status match; Actions has
# no header label but still needs to be accounted for so everything sums
# to 12: 5 + 2 + 2 + 3 = 12).
SORT_COLUMNS = [
    {'field': 'title', 'label': 'Dataset', 'col': 'col-md-5', 'align': 'start'},
    {'field': 'created', 'label': 'Submitted On', 'col': 'col-md-2', 'align': 'start'},
    {'field': 'status', 'label': 'Status', 'col': 'col-md-2', 'align': 'start'},
]


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
    datasets = datasets.prefetch_related('pre_submissions', 'status_history').order_by('-created')

    # Captured before the search filter below so a search that happens to
    # match zero datasets of a type doesn't make that type's tab (and, if
    # only one type is left, the whole tab bar) disappear while typing.
    types_present = {'recommend' if w else 'own' for w in datasets.values_list('is_wishlist', flat=True)}

    query = request.GET.get('q', '').strip()
    if query:
        # distinct() because the reverse join can otherwise duplicate a
        # Submission row if it ever ends up with more than one PreSubmission.
        datasets = datasets.filter(pre_submissions__dataset_title__icontains=query).distinct()

    datasets = list(datasets)
    status_labels = dict(SubmissionStatus.Status.choices)
    type_labels = dict(SUBMISSION_TYPE_CHOICES)
    for dataset in datasets:
        pre_submission = _get_pre_submission(dataset)
        dataset.dataset_title = pre_submission.dataset_title if pre_submission else ''
        dataset.owner_initials, dataset.owner_name = _owner_display(dataset.submitted_by)
        dataset.submission_type = 'recommend' if dataset.is_wishlist else 'own'
        current_status = _current_status(dataset)
        dataset.submission_status = current_status.status if current_status else None
        dataset.status_label = status_labels[dataset.submission_status]
        dataset.status_percent = STATUS_PROGRESS.get(dataset.submission_status)

    # Sort param convention: field name for ascending, "-field" for
    # descending. Falls back to the query's natural newest-first order
    # (same as an explicit "-created") for an empty/unrecognized value.
    sort_param = request.GET.get('sort', '')
    sort_field = sort_param.lstrip('-')
    sort_desc = sort_param.startswith('-')
    if sort_field not in SORT_FIELDS:
        sort_field, sort_desc = 'created', True
    datasets.sort(key=SORT_FIELDS[sort_field], reverse=sort_desc)

    # Clicking an unsorted column sorts it ascending; clicking the
    # already-active column flips its direction. Every other query param
    # (filters, search) is preserved.
    def _sort_url(field):
        active = sort_field == field
        next_desc = active and not sort_desc
        params = request.GET.copy()
        params['sort'] = f'-{field}' if next_desc else field
        return f'{request.path}?{params.urlencode()}'

    sort_columns = [
        {
            'field': col['field'],
            'label': col['label'],
            'col': col['col'],
            'align': col['align'],
            'url': _sort_url(col['field']),
            'active': sort_field == col['field'],
            'desc': sort_field == col['field'] and sort_desc,
        }
        for col in SORT_COLUMNS
    ]

    # Every tile is a toggle: clicking a value already selected removes it
    # from that field's list (deselect), clicking an unselected one adds it
    # (select), while every other field/value in the URL stays as-is.
    def _toggle_url(field, value, valid_values):
        params = request.GET.copy()
        current = [v for v in params.getlist(field) if v in valid_values]
        current = [v for v in current if v != value] if value in current else current + [value]
        params.setlist(field, current)
        return f'{request.path}?{params.urlencode()}' if params else request.path

    # Type tile counts are computed on the search-filtered set only (not
    # narrowed by status), so "My Submissions" + "Recommended Datasets"
    # always sum to "Total Datasets" regardless of any status tile selection.
    selected_types = [t for t in request.GET.getlist('type') if t in type_labels]

    # The "New..." button in the Active card relabels to match whichever
    # single type the user is filtered to; with no filter (or both types
    # selected) it falls back to the plain "New Submission" default.
    new_submission_label = 'New Wishlist Dataset' if selected_types == ['recommend'] else 'New Submission'

    type_filters = [
        {
            'value': value,
            'label': TYPE_META[value]['tile_label'],
            'icon': TYPE_META[value]['icon'],
            'color': TYPE_META[value]['color'],
            'count': sum(1 for d in datasets if d.submission_type == value),
            'toggle_url': _toggle_url('type', value, type_labels),
        }
        for value in type_labels
    ]
    type_filters = [f for f in type_filters if f['value'] in types_present]

    if selected_types:
        datasets = [d for d in datasets if d.submission_type in selected_types]

    # Status tile counts respect the current type selection (computed after
    # the type filter above) but not any status selection, so checking one
    # status tile doesn't change another status tile's own count.
    selected_statuses = [s for s in request.GET.getlist('status') if s in status_labels]
    status_filters = [
        {
            'value': status,
            'label': status_labels[status],
            'icon': STATUS_META[status]['icon'],
            'color': STATUS_META[status]['color'],
            'count': sum(1 for d in datasets if d.submission_status == status),
            'toggle_url': _toggle_url('status', status, status_labels),
        }
        for status in STATUS_ORDER
    ]
    status_filters = [f for f in status_filters if f['count']]

    if selected_statuses:
        datasets = [d for d in datasets if d.submission_status in selected_statuses]

    all_datasets_params = request.GET.copy()
    all_datasets_params.pop('status', None)
    all_datasets_params.pop('type', None)
    all_datasets_params.pop('q', None)
    all_datasets_url = f'{request.path}?{all_datasets_params.urlencode()}' if all_datasets_params else request.path

    # Lets the "Showing:" strip's search chip remove just the query while
    # keeping whatever type/status filters are also active.
    query_clear_params = request.GET.copy()
    query_clear_params.pop('q', None)
    query_clear_url = f'{request.path}?{query_clear_params.urlencode()}' if query_clear_params else request.path

    any_filter_selected = bool(selected_statuses or selected_types)

    def _status_query_url(statuses):
        params = request.GET.copy()
        params.setlist('status', statuses)
        return f'{request.path}?{params.urlencode()}'

    status_groups = []
    for card in CARD_DEFINITIONS:
        card_statuses = card['statuses']
        group_datasets = [d for d in datasets if d.submission_status in card_statuses]
        if not group_datasets:
            continue
        single_status = card_statuses[0] if len(card_statuses) == 1 else None
        status_groups.append({
            'key': card['key'],
            'value': single_status,
            'label': card.get('label') or status_labels[single_status],
            'icon': card.get('icon') or STATUS_META[single_status]['icon'],
            'color': card.get('color') or STATUS_META[single_status]['color'],
            'count': len(group_datasets),
            'datasets': group_datasets,
            'view_all_url': _status_query_url(card_statuses),
        })

    return render(request, 'datasubmit/submission_portal/my_datasets/home.html', {
        'status_groups': status_groups,
        'status_filters': status_filters,
        'type_filters': type_filters,
        'selected_statuses': selected_statuses,
        'selected_types': selected_types,
        'any_filter_selected': any_filter_selected,
        'all_datasets_url': all_datasets_url,
        'query': query,
        'query_clear_url': query_clear_url,
        'sort_columns': sort_columns,
        'new_submission_label': new_submission_label,
    })

@portal_view
def data_submission_portal_view(request, pk):
    dataset = _get_owned_submission(request, pk, prefetch=('locations', 'pre_submissions'))

    access_method_labels = dict(ACCESS_METHOD_CHOICES)
    locations = [
        {
            'location': loc.location,
            'access_method_label': access_method_labels.get(loc.access_method, loc.access_method),
            'readable': loc.readable,
            'reachable': loc.reachable,
        }
        for loc in dataset.locations.all()
    ]

    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-overview.html', {
        'dataset': dataset,
        'pre_submission': _get_pre_submission(dataset),
        'dataset_size_display': _format_dataset_size(dataset.dataset_size_mb),
        'locations': locations,
        'active_tab': 'Home',
    })

@portal_view
def data_submission_portal_files(request, pk):
    dataset = _get_owned_submission(request, pk, prefetch=('locations', 'pre_submissions'))

    access_method_labels = dict(ACCESS_METHOD_CHOICES)
    locations = [
        {
            'location': loc.location,
            'access_method_label': access_method_labels.get(loc.access_method, loc.access_method),
            'readable': loc.readable,
            'reachable': loc.reachable,
        }
        for loc in dataset.locations.all()
    ]

    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-files.html', {
        'dataset': dataset,
        'pre_submission': _get_pre_submission(dataset),
        'locations': locations,
        'active_tab': 'Files',
    })

@portal_view
def data_submission_portal_metadata(request, pk):
    dataset = _get_owned_submission(request, pk, prefetch=('pre_submissions',))
    return render(request, 'datasubmit/submission_portal/my_datasets/dataset-metadata.html', {
        'dataset': dataset,
        'pre_submission': _get_pre_submission(dataset),
        'active_tab': 'Metadata',
    })
