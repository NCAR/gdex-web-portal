# Developer Guide: `datasubmit` App

## 1. What it is and where it lives

`datasubmit` is a standard Django app inside the larger `gdexwebserver` project (a Wagtail-based monolith at `gdex-web-portal/gdex-web-portal/`). It implements the **Data Submission Portal** — the UI where researchers submit datasets to GDEX (or recommend datasets they don't own) and then track those submissions.

It's registered like any other app:
- `INSTALLED_APPS` in `gdexwebserver/settings/base.py:49` (and `local_dev.py:57`)
- Mounted at the URL root in `gdexwebserver/urls.py:32`: `path('', include('datasubmit.urls'))`
- Every user-facing route lives under `/submitportal/...`

## 2. Directory layout

```
datasubmit/
├── models.py            # 2 models: Submission, DatasetLocation
├── admin.py             # Django admin registration
├── apps.py              # standard AppConfig
├── services.py          # one function: calls GDEX's external check-access HTTP service
├── urls.py               # all /submitportal/... routes
├── migrations/           # 3 migrations, in sync with models.py
├── forms/                # form classes, split by wizard step
│   ├── __init__.py       # re-exports everything so views do `from ..forms import X`
│   ├── common.py         # shared choices/widgets/helpers
│   ├── advisor.py        # IntroForm, ZenodoChoiceForm
│   ├── basic_info.py     # BasicInfoForm
│   ├── access_info.py    # AccessInfoForm + access-method detection/verification
│   ├── contributors.py   # AuthorForm/AuthorFormSet/ContributorsMetaForm
│   └── policies.py       # PoliciesForm
├── views/                # views, split by portal section
│   ├── __init__.py       # re-exports everything so urls.py does `views.<name>`
│   ├── common.py         # portal_view decorator, ownership/session helpers
│   ├── my_datasets.py    # the dashboard + per-dataset detail pages
│   ├── submit.py         # the multi-step submission wizard (the bulk of the logic)
│   ├── budget_billing.py # stub page
│   ├── messages.py       # stub page
│   └── proposal_templates.py # stub page
├── static/datasubmit/css/datasubmit.css
└── templates/datasubmit/submission_portal/
    ├── portal_base.html          # sidebar shell, extends the project's base_fluid.html
    ├── my_datasets/              # dashboard + dataset detail templates
    ├── submit/                   # wizard step templates
    ├── budget_billing/home.html
    ├── messages/home.html
    └── proposal_templates/home.html
```

The `forms/` and `views/` packages are both organized the same way: **one submodule per portal section/wizard step**, all re-exported through `__init__.py` so consumers never need to know which file something actually lives in (`from ..forms import BasicInfoForm`, `views.data_submission_portal`, etc.).

## 3. Data model

Two models, `models.py`:

**`Submission`** — one row per submitted/recommended dataset.
- `submission_type`: `'own'` (submitting your own dataset) vs `'recommend'` (suggesting someone else's for GDEX to acquire) — this fork changes wizard behavior throughout.
- `submission_status` (`Status` enum): `pending_decision → in_progress → in_review → published`, plus `canceled`/`deleted` off to the side. Drives the dashboard's status pills and progress bars.
- `submission_decision` (`Decision` enum): `pending/approved/rejected` — independent of status.
- `dsid`: placeholder for the eventual GDEX dataset ID; nothing in the wizard sets it yet — staff populate it out-of-band.
- `dataset_title/abstract/details`, `dataset_size_mb`, plus boolean flags captured from the Advisor (`hpc_access`, `cif_fare_contributors`, `is_ncar_employee`) and the two agreement checkboxes.
- `submitted_by` is `SET_NULL` — a deleted user account doesn't cascade-delete their submissions.

**`DatasetLocation`** — one row per place the data physically lives, FK'd to `Submission` (`related_name='locations'`). A submission can have up to two (enforced only in the form/UI, not the schema — the model intentionally allows more, in case that cap changes later). Each row stores `location`, `access_method`, `access_verification` (`''`/`readable`/`reachable`), and `order`.

Both are registered in `admin.py` with `DatasetLocationInline` on the `Submission` admin page.

## 4. The `common.py` view helpers (read this before touching any view)

`views/common.py` is small but everything else depends on it:

- **`portal_view`** decorator: stacks `@never_cache` + `@login_required` on every portal view — except it skips the login requirement when `_portal_dev_mode()` is true. Apply this to any new view instead of hand-stacking decorators.
- **`_portal_dev_mode()`**: reads `settings.DATASUBMIT_SHOW_ALL_SUBMISSIONS`. Only `local_dev.py` sets this to `True` (because local dev has no login system at all — no allauth installed). `dev.py`/`production.py` never set it, so real deployments always get the secure per-user behavior.
- **`_agent_view_active(request)`**: superusers get a sidebar toggle to preview the portal as a normal customer would (own submissions only) vs. the default "agent" view (all submissions). Session-backed via `PORTAL_VIEW_MODE_SESSION_KEY`.
- **`_get_owned_submission(request, pk, prefetch=...)`**: the single choke point for "can this user see this submission" — used by every per-dataset detail view. Returns any submission in dev mode or agent view; otherwise 404s unless `submitted_by == request.user`.
- **`_format_dataset_size`**, **`_owner_display`**: display helpers.

If you add a new per-dataset page, route it through `_get_owned_submission` — don't write a new ownership check.

## 5. The "My Datasets" dashboard (`views/my_datasets.py`)

`data_submission_portal` (→ `my_datasets/home.html`) is the landing dashboard. It's entirely GET-param driven, no separate search/filter POST:

- **Search**: `?q=` filters `dataset_title__icontains`.
- **Type filter**: `?type=own&type=recommend` (repeatable) — toggle links computed by `_toggle_url`.
- **Status filter**: `?status=in_review` similarly.
- **Sort**: `?sort=field` / `?sort=-field`, driven by `SORT_FIELDS` (title/status/created/decision). Column headers are generated sort links via `_sort_url`.
- Datasets get annotated in-memory (not DB fields) with `.owner_initials`, `.status_label`, `.status_percent`, `.decision_label` before rendering.
- Results are grouped into **cards**: an "Active" card spanning `in_progress/pending_decision/in_review`, plus separate `published`/`canceled` cards (`CARD_DEFINITIONS`). Each dataset's own status still shows as a pill inside the shared Active card.

`data_submission_portal_view` / `_files` / `_metadata` are the three tabs of a single dataset's detail page, all extending `my_dataset_base.html` (which itself extends `portal_base.html`). `dataset-metadata.html` is a stub ("Metadata editing... isn't wired up yet").

`data_submission_portal_set_view_mode` handles the superuser agent/customer toggle POST, with open-redirect protection via `url_has_allowed_host_and_scheme`.

## 6. The submission wizard — this is the core of the app (`views/submit.py`)

This is by far the most complex file. The flow has **two conceptual stages**:

### Stage 1 — the Advisor (`/submitportal/submit/advisor/...`)
A five-question triage (`IntroForm`) that decides whether the user should even use GDEX's own form, or should be routed to Zenodo instead:
- `_bypasses_zenodo`: CIF/FARE-funded submissions always go straight to GDEX.
- `_qualifies_for_zenodo`: small (`< 50GB` via `ZENODO_SIZE_THRESHOLD_MB`), no-HPC-access datasets get offered Zenodo first (`data_submission_zenodo_recommendation`).
- `submission_content == 'software_only'` always routes to Zenodo next-steps, no recommendation screen.
- User's Zenodo choice (`ZenodoChoiceForm.continue_with_gdex`) branches to either `gdex-next-steps` or `zenodo-next-steps`.

**Recommendations (`submission_type == 'recommend'`) skip the Advisor entirely** — see `_wizard_gate_redirect`, which is the single access-control gate every wizard step calls.

### Stage 2 — the GDEX form itself (`/submitportal/submit/gdex-submission-form/<step_slug>/`)
Four steps, defined by parallel dicts keyed by step number:
```python
STEP_FORMS  = {1: BasicInfoForm, 3: AccessInfoForm, 4: PoliciesForm}
STEP_TITLES = {1: 'Basic Information', 2: 'Authors', 3: 'Dataset Access', 4: 'Terms & Conditions'}
STEP_SLUGS  = {1: 'basic-information', 2: 'contributors', 3: 'access-info', 4: 'terms-and-conditions'}
```
Step 2 (Authors/Contributors) is missing from `STEP_FORMS` deliberately — it uses a Django **formset**, not a plain form, so it gets its own dedicated view, `data_submission_contributors`, rather than going through the generic `gdex_submission_form_step`.

Key mechanics to understand:
- **`AUTHORS_STEP_ENABLED = False`**: the Authors step is currently switched off for *every* submission (not just recommendations). All its code (view, forms, template, URL) is intentionally kept intact — flip this one flag to re-enable it.
- **Session-backed wizard state**: everything typed so far lives in `request.session[SESSION_KEY]` (`'data_submission_wizard'`) as a dict keyed by step number as a *string* (`'0'` = advisor answers, `'welcome'` = submission_type, `'1'..'4'` = form steps, `'zenodo'` = Zenodo choice). Nothing touches the DB until the last step.
- **`_wizard_gate_redirect`**: called at the top of every step-3/4/contributors view. Walks backward through required earlier steps and Advisor/Zenodo gating, and redirects to whichever step is actually missing rather than letting you jump ahead via URL.
- **Progress bar math**: `_progress_steps`/`_step_progress` exist because skipping step 2 (Authors) for recommendations leaves a *gap* in the real step numbers, but the progress bar UI still needs clean sequential numbering (1,2,3...) — so each progress entry carries both `num` (display position) and `real_num` (actual routing step).
- **Final submission** happens inside `gdex_submission_form_step` when `step == TOTAL_STEPS` (step 4) succeeds: it reads all the session data back out, computes `dataset_size_mb`/`hpc_access`/etc. differently depending on `is_recommendation` (recommendations collect size directly in Basic Info instead of via the Advisor), creates the `Submission` row plus one or two `DatasetLocation` rows, clears the session key, and stashes `last_submission_id` in the session for the confirmation page to read once and discard.

**All Stage-2 wizard views are currently gated behind `@user_passes_test(lambda u: _portal_dev_mode() or u.is_superuser)`** — explicitly marked with `# TODO: temporary gate for prod testing before public launch -- remove this line to reopen to all logged-in users.` This is pre-launch scaffolding, not permanent behavior — expect it to be removed later.

## 7. Forms package details worth knowing

- **`forms/common.py`**: `mark_invalid_fields(form)` is called from views after a failed `is_valid()` — it adds `is-invalid` class + `aria-invalid`/`aria-describedby` for accessibility. Any new template rendering form errors must render an error container with `id="{{ field.auto_id }}_error"` for the `aria-describedby` link to resolve. `PlaceholderSelect` is a custom `Select` widget that disables the blank "Select an option" choice like a real placeholder.
- **`forms/access_info.py`**: the interesting one. **Access method is no longer a user-chosen dropdown — it's inferred from the URL/path they type**, via `detect_access_method()` matching against ordered regex patterns (`ACCESS_METHOD_DETECTION_ORDER`: https → ftp/sftp → s3 → path → doi → fallback `other`). For `path` (must be under `/glade/`) and `https`, `AccessInfoForm.clean()` calls `services.check_path_access()` — a **hard server-side gate**: submission cannot proceed past this step if the location isn't actually reachable/readable. This same detection logic is duplicated in JS in the template purely for live help-text/UX; the real enforcement is server-side.
- **`forms/contributors.py`**: `AuthorFormSet` is a `formset_factory` with `can_order`/`can_delete`, `min_num=1`. The ORDER/DELETE management fields are hidden and driven entirely by JS in the template.
- **`forms/policies.py`**: `data_deposit_agreement` becomes conditionally required based on `is_ncar_employee` (non-UCAR contributors must agree; UCAR employees don't need to).
- **`forms/basic_info.py`**: `dataset_size`/`dataset_size_units` are conditionally added/removed depending on whether the Advisor already collected them (`is_recommendation` flag).

## 8. Templates & frontend conventions

- Everything extends `datasubmit/submission_portal/portal_base.html`, which itself extends the project-wide `base_fluid.html`. `portal_base.html` renders the left sidebar nav (My Datasets / Submit Data / Messages / Budget Tool, with a commented-out Proposal Templates link) and, for superusers, the agent/customer view-mode toggle.
- Detail pages (`Overview`/`Files`/`Metadata` tabs) extend `my_datasets/my_dataset_base.html`, which renders the dataset header + tab nav, then yields to a `dataset_content` block.
- Bootstrap-based (`.card.rounded-4`, `.btn-outline-primary`, FontAwesome icons). **Note**: `gdexwebserver`'s global `main.css` redefines Bootstrap's `p-*`/`m-*` spacing utilities with larger `!important` values than stock Bootstrap — relevant if spacing looks off compared to plain Bootstrap docs.
- Wizard step template (`gdex_submission_form_step.html`) is the most JS-heavy: it live-updates location help text and access-method detection client-side (mirroring `detect_access_method()` in Python — **keep these two in sync if you ever change the regex patterns**), shows a "reading files…" spinner on submit for checked access methods, handles the "Add another location" reveal (capped at 2), and drives a live character counter for fields whose `maxlength` Django would otherwise render as a hard HTML truncation limit (deliberately swapped to `data-maxlength` in `BasicInfoForm.__init__`).
- `access_method_info` / `access_method_detection_order` are passed to the template via Django's `json_script` filter and read by the JS as `#access-method-info-data` / `#access-method-detection-order-data`.

## 9. External dependency

`services.py` is the only outbound integration: a GET to `https://gdex-services.k8s.ucar.edu/files/check-access` (GDEX's own microservice), used exclusively by `AccessInfoForm.clean()`. It returns different JSON shapes depending on whether you asked about a `/glade` path (`globally_readable`, recursive scan capped at `CHECK_ACCESS_MAX_RESULTS=10` files) or an `https` URL (`accessible`, a plain reachability ping — no scan). Timeouts and request errors are caught and turned into specific user-facing messages in `access_info.py`'s `_check_location`.

## 10. Local dev specifics

`gdexwebserver/settings/local_dev.py` sets `DATASUBMIT_SHOW_ALL_SUBMISSIONS = True` because local dev has no login app installed at all and its SQLite fixtures all have `submitted_by=None`. This single flag, read everywhere via `_portal_dev_mode()`, disables both the login requirement and the per-user ownership filter — it does not exist in `base.py`/`production.py`, so real environments always get the secure behavior. `DATASUBMIT_SIDEBAR_LOGO_URL` / `DATASUBMIT_DATASET_THUMBNAIL_URL` are also swapped locally since the real `MEDIA_ROOT` path doesn't exist on a dev machine.

## 11. Migrations

Only 3 migrations, all current with `models.py` — `0001_initial` → `0002` adds `created`/`submitted_by` → `0003` adds `submission_decision`/`submission_status`. No pending schema drift.

---

**If you're about to extend this app**, the two files to read first are `views/common.py` (access control) and `views/submit.py` (wizard flow/session state) — nearly everything else is a thinner, more self-contained layer on top of those two.
