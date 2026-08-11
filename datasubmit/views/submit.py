from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import (
    ACCESS_METHOD_CHOICES,
    ACCESS_METHOD_DETECTION_ORDER,
    ACCESS_METHOD_INFO,
    SUBMISSION_TYPE_CHOICES,
    AccessInfoForm,
    AuthorFormSet,
    BasicInfoForm,
    ContributorsMetaForm,
    IntroForm,
    PoliciesForm,
    ZenodoChoiceForm,
    convert_dataset_size_to_mb,
    mark_invalid_fields,
)
from ..models import DatasetLocation, PreSubmission, Submission, SubmissionStatus
from .common import _format_dataset_size, _get_pre_submission, _portal_dev_mode, portal_view

# Small, HPC-independent datasets can be archived faster via Zenodo than through
# the full GDEX intake process, so those submitters get offered that option first.
ZENODO_SIZE_THRESHOLD_MB = 50 * 1024

# Authors is turned off for every submission type -- flip this back to True to
# restore it as a real step. Deliberately not removing any of the Authors code
# (view, forms, template, URL) so re-enabling is just this one flag.
AUTHORS_STEP_ENABLED = False

# Step 2 (Contributors) is handled by its own view (data_submission_contributors) since it's
# a formset, not a plain Form, so it's deliberately absent from STEP_FORMS.
STEP_FORMS = {
    1: BasicInfoForm,
    3: AccessInfoForm,
    4: PoliciesForm,
}
STEP_TITLES = {
    1: 'Basic Information',
    2: 'Authors',
    3: 'Dataset Access',
    4: 'Terms & Conditions',
}
STEP_SLUGS = {
    1: 'basic-information',
    2: 'contributors',
    3: 'access-info',
    4: 'terms-and-conditions',
}
SLUG_TO_STEP = {slug: num for num, slug in STEP_SLUGS.items()}
TOTAL_STEPS = len(STEP_TITLES)
SESSION_KEY = 'data_submission_wizard'

# Confirmation isn't a form step, but it's shown as the final entry on the progress bar.
CONFIRMATION_STEP = TOTAL_STEPS + 1
PROGRESS_STEPS = [{'num': num, 'title': STEP_TITLES[num]} for num in sorted(STEP_TITLES)] + [
    {'num': CONFIRMATION_STEP, 'title': 'Confirmation'},
]


def _skips_authors_step(is_recommendation):
    """Recommendations always skip Authors (step 2) -- there's no contributor
    to name for a dataset you're only suggesting. Every other submission also
    skips it for now because AUTHORS_STEP_ENABLED is off."""
    return is_recommendation or not AUTHORS_STEP_ENABLED


def _progress_steps(is_recommendation):
    """When Authors (step 2) is skipped, it shouldn't show up on the progress
    bar either. Each returned dict's 'num' is a clean sequential display
    position (1, 2, 3...) for the circle label; 'real_num' is the actual step
    number routing/session data keys off of -- templates must match the
    active step against real_num, not num, since skipping step 2 leaves a gap
    in real_num."""
    steps = [s for s in PROGRESS_STEPS if not _skips_authors_step(is_recommendation) or s['num'] != 2]
    return [{'num': i + 1, 'real_num': s['num'], 'title': s['title']} for i, s in enumerate(steps)]


def _step_url(step):
    return reverse('data-submission-step', kwargs={'step_slug': STEP_SLUGS[step]})


def _step_progress(steps, real_num):
    """Maps the active step's real_num to its sequential display position in
    `steps` (matching the numeral shown in its progress-bar circle), for the
    screen-reader-only "Step X of Y" text -- real_num alone isn't it, since
    skipping Authors for recommendations leaves a gap in real_num."""
    for s in steps:
        if s['real_num'] == real_num:
            return s['num'], len(steps)
    return real_num, len(steps)


def _bypasses_zenodo(intro_info):
    """CIF/FARE-affiliated submissions always go to GDEX, skipping the Zenodo detour entirely."""
    return intro_info.get('cif_fare_contributors') == 'True'


def _qualifies_for_zenodo(intro_info):
    size_mb = convert_dataset_size_to_mb(intro_info['dataset_size'], intro_info['dataset_size_units'])
    return size_mb < ZENODO_SIZE_THRESHOLD_MB and intro_info['hpc_access'] == 'False'


def _zenodo_reason(wizard_data):
    """Why the user landed on the Zenodo next-steps page, or None if they shouldn't be there."""
    intro_info = wizard_data.get('0')
    if not intro_info or _bypasses_zenodo(intro_info):
        return None
    if intro_info.get('submission_content') == 'software_only':
        return 'software'
    if wizard_data.get('zenodo', {}).get('continue_with_gdex') == 'False':
        return 'declined_gdex'
    return None


def _wizard_gate_redirect(wizard_data, step):
    """Shared access control for any step (1-4) of the GDEX wizard. Returns a redirect, or None if allowed."""
    is_recommendation = wizard_data.get('welcome', {}).get('submission_type') == 'recommend'

    # Recommendations skip the Advisor entirely, so none of its
    # answers (or the Zenodo detour that depends on them) apply.
    if not is_recommendation:
        if '0' not in wizard_data:
            return redirect('data-submission-advisor')

        if not _bypasses_zenodo(wizard_data['0']):
            if wizard_data['0'].get('submission_content') == 'software_only':
                return redirect('data-submission-zenodo-next-steps')

            if _qualifies_for_zenodo(wizard_data['0']):
                zenodo_choice = wizard_data.get('zenodo', {}).get('continue_with_gdex')
                if zenodo_choice == 'False':
                    return redirect('data-submission-zenodo-next-steps')
                if zenodo_choice != 'True':
                    return redirect('data-submission-zenodo-recommendation')

    for earlier_step in range(1, step):
        if _skips_authors_step(is_recommendation) and earlier_step == 2:
            # Authors is skipped -- it'll never be in wizard_data, and
            # that's expected, not a gap.
            continue
        if str(earlier_step) not in wizard_data:
            if is_recommendation:
                return redirect(_step_url(1))
            return redirect('data-submission-advisor')

    return None


@portal_view
def data_submission_welcome(request):
    """Landing page with the Submit Data / Suggest Dataset cards. Deliberately
    a separate URL from 'data-submission-advisor' -- the various mid-flow
    redirects that send a user back here when session data is missing should
    land them on the cards, not re-explain the process every time.

    Each card links straight here with ?type=own or ?type=recommend rather
    than posting a form -- there's nothing to validate beyond "is this one of
    the two known values", so a plain link is simpler than a form only to
    immediately redirect on submit."""
    requested_type = request.GET.get('type')
    if requested_type in dict(SUBMISSION_TYPE_CHOICES):
        wizard_data = request.session.get(SESSION_KEY, {})
        wizard_data['welcome'] = {'submission_type': requested_type}
        request.session[SESSION_KEY] = wizard_data
        if requested_type == 'recommend':
            # Recommendations skip the Advisor entirely and go straight
            # into the GDEX form, starting at Basic Information.
            return redirect(_step_url(1))
        return redirect('data-submission-advisor')

    return render(request, 'datasubmit/submission_portal/submit/data_submission_welcome.html')

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def submission_confirmation(request):
    submission_id = request.session.pop('last_submission_id', None)
    submission = None
    if submission_id:
        submission = Submission.objects.prefetch_related('locations', 'pre_submissions').filter(pk=submission_id).first()

    access_method_labels = dict(ACCESS_METHOD_CHOICES)
    locations = []
    pre_submission = None
    if submission:
        pre_submission = _get_pre_submission(submission)
        for loc in submission.locations.all():
            locations.append({
                'location': loc.location,
                'access_method_label': access_method_labels.get(loc.access_method, loc.access_method),
                'readable': loc.readable,
                'reachable': loc.reachable,
            })

    # The wizard session (including 'welcome') is already cleared by the time
    # we get here, so read the recommendation flag off the saved row instead.
    is_recommendation = bool(submission and submission.is_wishlist)
    steps = _progress_steps(is_recommendation)
    step_display, step_count = _step_progress(steps, CONFIRMATION_STEP)

    return render(request, 'datasubmit/submission_portal/submit/submission_confirmation.html', {
        'steps': steps,
        'step': CONFIRMATION_STEP,
        'step_display': step_display,
        'step_count': step_count,
        'submission': submission,
        'pre_submission': pre_submission,
        'dataset_size_display': _format_dataset_size(submission.dataset_size_mb) if submission else None,
        'locations': locations,
    })

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def submission_advisor(request):
    wizard_data = request.session.get(SESSION_KEY, {})

    if request.method == 'POST':
        form = IntroForm(request.POST)
        if form.is_valid():
            wizard_data['0'] = form.cleaned_data
            wizard_data.pop('zenodo', None)
            request.session[SESSION_KEY] = wizard_data
            if _bypasses_zenodo(form.cleaned_data):
                return redirect('data-submission-gdex-next-steps')
            if form.cleaned_data['submission_content'] == 'software_only':
                return redirect('data-submission-zenodo-next-steps')
            if _qualifies_for_zenodo(form.cleaned_data):
                return redirect('data-submission-zenodo-recommendation')
            return redirect('data-submission-gdex-next-steps')

        mark_invalid_fields(form)
    else:
        form = IntroForm(initial=wizard_data.get('0', {}))

    return render(request, 'datasubmit/submission_portal/submit/submission_advisor.html', {
        'form': form,
        'has_help_text': any(field.help_text for field in form),
    })

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def data_submission_zenodo_recommendation(request):
    wizard_data = request.session.get(SESSION_KEY, {})

    if '0' not in wizard_data:
        return redirect('data-submission-advisor')
    if _bypasses_zenodo(wizard_data['0']):
        return redirect('data-submission-gdex-next-steps')
    if wizard_data['0'].get('submission_content') == 'software_only':
        return redirect('data-submission-zenodo-next-steps')
    if not _qualifies_for_zenodo(wizard_data['0']):
        return redirect('data-submission-gdex-next-steps')

    if request.method == 'POST':
        form = ZenodoChoiceForm(request.POST)
        if form.is_valid():
            wizard_data['zenodo'] = form.cleaned_data
            request.session[SESSION_KEY] = wizard_data
            if form.cleaned_data['continue_with_gdex'] == 'True':
                return redirect('data-submission-gdex-next-steps')
            return redirect('data-submission-zenodo-next-steps')

        mark_invalid_fields(form)
    else:
        form = ZenodoChoiceForm(initial=wizard_data.get('zenodo', {}))

    return render(request, 'datasubmit/submission_portal/submit/data_submission_zenodo_recommendation.html', {'form': form})

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def data_submission_zenodo_next_steps(request):
    wizard_data = request.session.get(SESSION_KEY, {})
    reason = _zenodo_reason(wizard_data)
    if reason is None:
        return redirect('data-submission-advisor')

    return render(request, 'datasubmit/submission_portal/submit/data_submission_zenodo_next_steps.html', {'reason': reason})

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def data_submission_gdex_next_steps(request):
    wizard_data = request.session.get(SESSION_KEY, {})
    if '0' not in wizard_data:
        return redirect('data-submission-advisor')

    return render(request, 'datasubmit/submission_portal/submit/data_submission_gdex_next_steps.html', {'start_url': _step_url(1)})

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def data_submission_contributors(request):
    step = 2
    wizard_data = request.session.get(SESSION_KEY, {})
    gate = _wizard_gate_redirect(wizard_data, step)
    if gate:
        return gate

    is_recommendation = wizard_data.get('welcome', {}).get('submission_type') == 'recommend'
    if _skips_authors_step(is_recommendation):
        # Not a real destination right now -- see AUTHORS_STEP_ENABLED. Send
        # them onward rather than leaving this URL dead.
        return redirect(_step_url(3))

    saved = wizard_data.get(str(step), {})
    saved_meta = saved.get('meta', {})
    saved_authors = saved.get('authors') or [{}]

    if request.method == 'POST':
        meta_form = ContributorsMetaForm(request.POST)
        is_organization = request.POST.get('submitted_by_organization') == 'True'
        formset = AuthorFormSet(request.POST, form_kwargs={'is_organization': is_organization})

        if meta_form.is_valid() and formset.is_valid():
            ordered_authors = []
            kept_forms = [f for f in formset.forms if f.cleaned_data and not f.cleaned_data.get('DELETE')]
            for form in sorted(kept_forms, key=lambda f: f.cleaned_data.get('ORDER') or 0):
                author_data = form.cleaned_data.copy()
                author_data.pop('ORDER', None)
                author_data.pop('DELETE', None)
                ordered_authors.append(author_data)

            wizard_data[str(step)] = {'meta': meta_form.cleaned_data, 'authors': ordered_authors}
            request.session[SESSION_KEY] = wizard_data
            return redirect(_step_url(step + 1))

        mark_invalid_fields(meta_form)
        for form in formset.forms:
            mark_invalid_fields(form)
    else:
        meta_form = ContributorsMetaForm(initial=saved_meta)
        is_organization = saved_meta.get('submitted_by_organization') == 'True'
        formset = AuthorFormSet(initial=saved_authors, form_kwargs={'is_organization': is_organization})

    steps = _progress_steps(False)
    step_display, step_count = _step_progress(steps, step)

    return render(request, 'datasubmit/submission_portal/submit/data_submission_contributors.html', {
        'meta_form': meta_form,
        'formset': formset,
        'step': step,
        'step_title': STEP_TITLES[step],
        'steps': steps,
        'step_display': step_display,
        'step_count': step_count,
        'total_steps': TOTAL_STEPS,
        'is_last_step': step == TOTAL_STEPS,
        'prev_url': _step_url(step - 1),
    })

@portal_view
# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.
@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)
def gdex_submission_form_step(request, step_slug):
    if step_slug not in SLUG_TO_STEP:
        raise Http404
    step = SLUG_TO_STEP[step_slug]

    wizard_data = request.session.get(SESSION_KEY, {})
    gate = _wizard_gate_redirect(wizard_data, step)
    if gate:
        return gate

    is_recommendation = wizard_data.get('welcome', {}).get('submission_type') == 'recommend'

    FormClass = STEP_FORMS[step]
    form_kwargs = {}
    if step == 1:
        form_kwargs['is_recommendation'] = is_recommendation
    if step == 4:
        form_kwargs['is_ncar_employee'] = wizard_data.get('0', {}).get('is_ncar_employee')

    if request.method == 'POST':
        form = FormClass(request.POST, **form_kwargs)
        if form.is_valid():
            wizard_data[str(step)] = form.cleaned_data
            request.session[SESSION_KEY] = wizard_data

            if step == TOTAL_STEPS:
                intro_info = wizard_data.get('0', {})
                basic_info = wizard_data['1']
                access_info = wizard_data['3']
                policies_info = wizard_data['4']

                if is_recommendation:
                    # No Advisor answers to draw on -- Basic Information
                    # collected dataset size directly instead, and the
                    # HPC/CIF-FARE/employee questions just don't apply.
                    dataset_size_mb = convert_dataset_size_to_mb(
                        basic_info['dataset_size'], basic_info['dataset_size_units']
                    )
                    hpc_access = False
                    cif_fare_contributors = False
                    is_ncar_employee = False
                else:
                    dataset_size_mb = convert_dataset_size_to_mb(
                        intro_info['dataset_size'], intro_info['dataset_size_units']
                    )
                    hpc_access = intro_info['hpc_access'] == 'True'
                    cif_fare_contributors = intro_info['cif_fare_contributors'] == 'True'
                    is_ncar_employee = intro_info['is_ncar_employee'] == 'True'

                submission = Submission.objects.create(
                    submitted_by=request.user,
                    is_wishlist=wizard_data.get('welcome', {}).get('submission_type') == 'recommend',
                    dataset_size_mb=dataset_size_mb,
                )
                SubmissionStatus.objects.create(
                    submission=submission,
                    status=SubmissionStatus.Status.PENDING_DECISION,
                )
                PreSubmission.objects.create(
                    submission=submission,
                    dataset_title=basic_info['dataset_title'],
                    dataset_abstract=basic_info['dataset_abstract'],
                    dataset_details=basic_info['dataset_details'],
                    hpc_access=hpc_access,
                    cif_fare_contributors=cif_fare_contributors,
                    is_ncar_employee=is_ncar_employee,
                    data_policy_agreement=policies_info['data_policy_agreement'],
                    data_deposit_agreement=policies_info['data_deposit_agreement'],
                )
                verification = access_info.get('access_verification', '')
                DatasetLocation.objects.create(
                    submission=submission,
                    location=access_info['dataset_location'],
                    access_method=access_info['access_method'],
                    readable=verification == 'readable',
                    reachable=verification == 'reachable',
                    order=0,
                )
                if access_info.get('dataset_location_2'):
                    verification_2 = access_info.get('access_verification_2', '')
                    DatasetLocation.objects.create(
                        submission=submission,
                        location=access_info['dataset_location_2'],
                        access_method=access_info.get('access_method_2', ''),
                        readable=verification_2 == 'readable',
                        reachable=verification_2 == 'reachable',
                        order=1,
                    )
                del request.session[SESSION_KEY]
                request.session['last_submission_id'] = submission.id
                return redirect('data-submission-confirmation')

            if step == 1 and _skips_authors_step(is_recommendation):
                # Skip Authors -- straight to Dataset Access.
                return redirect(_step_url(3))

            return redirect(_step_url(step + 1))

        mark_invalid_fields(form)
    else:
        form = FormClass(initial=wizard_data.get(str(step), {}), **form_kwargs)

    if step == 3 and is_recommendation:
        # Authors (step 2) was skipped -- back goes to Basic Information, not Authors.
        prev_url = _step_url(1)
    elif step > 1:
        prev_url = _step_url(step - 1)
    else:
        prev_url = reverse('data-submission-welcome') if is_recommendation else reverse('data-submission-advisor')

    steps = _progress_steps(is_recommendation)
    step_display, step_count = _step_progress(steps, step)

    return render(request, 'datasubmit/submission_portal/submit/gdex_submission_form_step.html', {
        'form': form,
        'step': step,
        'step_title': STEP_TITLES[step],
        'steps': steps,
        'step_display': step_display,
        'step_count': step_count,
        'total_steps': TOTAL_STEPS,
        'is_last_step': step == TOTAL_STEPS,
        'prev_url': prev_url,
        'has_help_text': any(field.help_text for field in form),
        'show_deposit_agreement': step == 4 and wizard_data.get('0', {}).get('is_ncar_employee') == 'False',
        'access_method_info': {
            key: {'help_text': info['help_text'], 'placeholder': info['placeholder'], 'pattern': info['pattern']}
            for key, info in ACCESS_METHOD_INFO.items()
        },
        'access_method_detection_order': ACCESS_METHOD_DETECTION_ORDER,
    })
