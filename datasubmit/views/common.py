from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache

from ..models import Submission

PORTAL_VIEW_MODE_SESSION_KEY = 'datasubmit_portal_view_mode'


def _agent_view_active(request):
    """Superusers can flip the sidebar toggle to preview My Datasets the way
    a regular submitter sees it (their own submissions only). Everyone else
    always sees only their own submissions; superusers default to the agent
    side (all submissions) until they flip the toggle to customer."""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return False
    return request.session.get(PORTAL_VIEW_MODE_SESSION_KEY, 'agent') != 'customer'


def _portal_dev_mode():
    """True only under gdexwebserver/settings/local_dev.py, which installs no
    login system at all (no allauth/accounts app -- see that file's own
    docstring). Every /submitportal/ view and dataset lookup branches on this
    so local testing works without a real login, while dev.py/production.py
    (where the setting is simply undefined) always get the real, secure
    per-user behavior."""
    return getattr(settings, 'DATASUBMIT_SHOW_ALL_SUBMISSIONS', False)


def portal_view(view_func):
    """Every /submitportal/ view renders account-specific data, so bundle the
    two things that implies: never cache it, and require login -- except in
    local dev, where there's no login system to require (see
    _portal_dev_mode). Apply this to every new data_submission_portal_* view
    instead of stacking @login_required/@never_cache by hand, so the gate
    can't be forgotten the way it was for the first round of these views."""
    @never_cache
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if _portal_dev_mode():
            return view_func(request, *args, **kwargs)
        return login_required(view_func)(request, *args, **kwargs)
    return wrapped


def _get_owned_submission(request, pk, prefetch=()):
    """Fetch a Submission by pk, scoped to the requesting user -- except in
    local dev (_portal_dev_mode) or when a superuser has the agent-view
    toggle on (_agent_view_active), where any submission is fair game.
    Centralizes the ownership check so every per-dataset portal view
    (overview/files/metadata/...) enforces it the same way by construction,
    rather than each view remembering its own filter."""
    qs = Submission.objects.all()
    if prefetch:
        qs = qs.prefetch_related(*prefetch)
    if _portal_dev_mode() or _agent_view_active(request):
        return get_object_or_404(qs, pk=pk)
    return get_object_or_404(qs, pk=pk, submitted_by=request.user)


def _get_pre_submission(dataset):
    """The PreSubmission row holding `dataset`'s descriptive fields
    (title/abstract/details/etc.) -- FK'd as a to-many for schema
    flexibility, but the wizard only ever creates one per Submission.
    Uses .all() rather than .first() so a prefetch_related('pre_submissions')
    on the caller's queryset is actually used instead of issuing a new query
    (.first() adds its own ordering, which bypasses the prefetch cache)."""
    pre_submissions = list(dataset.pre_submissions.all())
    return pre_submissions[0] if pre_submissions else None


def _current_status(submission):
    """The most recent entry in a submission's status history -- there's no
    single current-status field, since GDEX tracks every status change over
    time rather than overwriting one column. Uses .all() rather than an
    ordered query so a prefetch_related('status_history') on the caller's
    queryset is actually used instead of issuing a new query per submission."""
    history = list(submission.status_history.all())
    return max(history, key=lambda s: s.timestamp) if history else None


def _format_dataset_size(size_mb):
    if size_mb >= 1024 * 1024:
        return f"{size_mb / (1024 * 1024):.2f} TB"
    if size_mb >= 1024:
        return f"{size_mb / 1024:.2f} GB"
    return f"{size_mb:.2f} MB"


def _owner_display(user):
    """(initials, display name) for a submission's owner avatar/label --
    submitted_by is SET_NULL, so a deleted account still needs something
    presentable rather than a template error."""
    if not user:
        return '?', 'Unknown'
    name = user.get_full_name().strip() or user.get_username()
    initials = ''.join(part[0].upper() for part in name.split()[:2]) or '?'
    return initials, name
