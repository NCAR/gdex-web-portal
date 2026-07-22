import re

import requests

from django import forms
from django.core.validators import RegexValidator

from .services import check_path_access

orcid_validator = RegexValidator(
    regex=r'^\d{4}-\d{4}-\d{4}-\d{4}$',
    message="Enter a valid ORCID iD in the format 0000-0000-0000-0000.",
)

ACCESS_METHOD_CHOICES = [
    ('', 'Select an option'),
    ('https', 'HTTPS'),
    ('ftp_sftp', 'FTP/SFTP'),
    ('s3', 'Amazon S3'),
    ('path', 'Absolute Linux Path (/glade only)'),
    ('doi', 'DOI (if applicable)'),
    ('other', 'Other'),
]

# Shown live under Dataset Location as the user changes Access Method (see the
# template's JS) and also used server-side in AccessInfoForm.clean() to pick
# which pattern the location must match.
ACCESS_METHOD_INFO = {
    'https': {
        'help_text': "Provide the full HTTPS URL where the dataset can be downloaded (e.g. https://example.edu/data/file.nc).",
        'placeholder': "https://example.edu/data/file.nc",
        'pattern': r'^https://\S+$',
        'error': "Enter a valid HTTPS URL, e.g. https://example.edu/data/file.nc.",
    },
    'ftp_sftp': {
        'help_text': "Provide the full FTP or SFTP address, including host and path (e.g. sftp://ftp.example.edu/data/file.nc).",
        'placeholder': "sftp://ftp.example.edu/data/file.nc",
        'pattern': r'^s?ftp://\S+$',
        'error': "Enter a valid FTP or SFTP address, e.g. sftp://ftp.example.edu/data/file.nc.",
    },
    's3': {
        'help_text': "Provide the Amazon S3 URI for the object or bucket (e.g. s3://my-bucket/path/to/file.nc).",
        'placeholder': "s3://my-bucket/path/to/file.nc",
        'pattern': r'^s3://\S+$',
        'error': "Enter a valid S3 URI, e.g. s3://my-bucket/path/to/file.nc.",
    },
    'path': {
        'help_text': "Only absolute paths under /glade are accepted — no other locations (e.g. /home, /tmp, "
        "external drives). Provide the full path where the dataset is stored (e.g. /glade/campaign/.../file.nc), "
        "and ensure 'others' have read and execute permissions so we can access and review the data.",
        'placeholder': "/glade/campaign/...",
        'pattern': r'^/glade/\S+$',
        'error': "Only /glade paths are accepted. Enter an absolute path starting with '/glade/', "
        "e.g. /glade/campaign/.../file.nc.",
    },
    'doi': {
        'help_text': "Provide the DOI (e.g. 10.1234/abcd) or the full https://doi.org/... URL, if one has been assigned.",
        'placeholder': "10.1234/abcd",
        'pattern': r'^(10\.\d{4,9}/\S+|https://doi\.org/10\.\d{4,9}/\S+)$',
        'error': "Enter a valid DOI, e.g. 10.1234/abcd, or a full https://doi.org/... URL.",
    },
    'other': {
        'help_text': "Describe how the dataset can be accessed.",
        'placeholder': "Describe how to access the dataset",
        'pattern': None,
        'error': None,
    },
}

# Checked in this order (most specific patterns first) -- 'other' isn't
# tried, it's the fallback when nothing else matches.
ACCESS_METHOD_DETECTION_ORDER = ['https', 'ftp_sftp', 's3', 'path', 'doi']


def detect_access_method(location):
    """Access method is no longer a user choice -- it's inferred from what
    they type as the dataset location."""
    for method in ACCESS_METHOD_DETECTION_ORDER:
        if re.match(ACCESS_METHOD_INFO[method]['pattern'], location):
            return method
    return 'other'


YES_NO_CHOICES = [
        ('', 'Select an option'),
        (True, 'Yes'),
        (False, 'No'),
    ]

HPC_ACCESS_CHOICES = [
    ('', 'Select an option'),
    (True, "Yes, I need HPC access"),
    (False, "No, I don't need HPC access"),
]

SUBMISSION_CONTENT_CHOICES = [
    ('', 'Select an option'),
    ('dataset', 'Dataset'),
    ('software_only', 'Software only'),
    ('software_and_dataset', 'Software + Dataset'),
]

# 1024-based (binary) multipliers, matching typical HPC/archive file-size conventions.
DATASET_SIZE_UNIT_TO_MB = {
    'MB': 1,
    'GB': 1024,
    'TB': 1024 ** 2,
    'PB': 1024 ** 3,
}
DATASET_SIZE_UNIT_CHOICES = [('', 'Select a unit')] + [(unit, unit) for unit in DATASET_SIZE_UNIT_TO_MB]


def convert_dataset_size_to_mb(size, unit):
    return size * DATASET_SIZE_UNIT_TO_MB[unit]


def mark_invalid_fields(form):
    """Called from views.py after a failed form.is_valid(). Adds the visual
    is-invalid border sighted users already got, plus aria-invalid and
    aria-describedby pointing at that field's error container -- so screen
    readers get the same "this field failed" signal instead of just a color
    change. Templates must render the matching error container with
    id="{{ field.auto_id }}_error" for the describedby link to resolve."""
    for field_name in form.errors:
        field = form[field_name]
        widget = field.field.widget
        widget.attrs['class'] = (widget.attrs.get('class', '') + ' is-invalid').strip()
        widget.attrs['aria-invalid'] = 'true'
        widget.attrs['aria-describedby'] = f'{field.auto_id}_error'


class PlaceholderSelect(forms.Select):
    """A <select> whose blank choice renders disabled, like a text input's placeholder."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value == '':
            option['attrs']['disabled'] = True
        return option


class IntroForm(forms.Form):
    dataset_size = forms.IntegerField(
        label="Approximate Dataset Size:",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-lg"}),
        help_text="This is an approximation and will be verified later in the process.",
    )

    dataset_size_units = forms.ChoiceField(
        label="Units",
        choices=DATASET_SIZE_UNIT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
    )

    cif_fare_contributors = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        help_text=(
            ' To check, review your NSF award documentation or search your award in the NSF '
            'Award Search database. '
            '<a href="https://www.nsf.gov/funding/opportunities/fare-facilities-atmospheric-research-education" '
            'target="_blank" rel="noopener" '
            'aria-label="Learn more about the FARE program (opens in a new tab)">'
            '<i class="fas fa-external-link-alt" aria-hidden="true"></i></a>'

        ),
        label= "Is this project part of, or funded by, the NSF Community Instrument Facility (CIF) or Facilities for Atmospheric Research and Education (FARE) programs?"
    )

    hpc_access = forms.ChoiceField(
        choices=HPC_ACCESS_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        help_text=(
            ' Answer Yes if you expect to access, analyze, process, or visualize the archived '
            'data using NCAR\'s HPC resources. '
            '<a href="https://arc.ucar.edu/resources" target="_blank" rel="noopener" '
            'aria-label="Learn more about NCAR HPC Resources (opens in a new tab)">'
            '<i class="fas fa-external-link-alt" aria-hidden="true"></i></a>'
            '<br> This allows the archived data to be available '
            'directly on NCAR\'s computing systems without requiring you to download or transfer '
            'it elsewhere. Answer No if you do not need continued access to the archived data '
            'through NCAR\'s HPCs. '

        ),
        label= "Will you need access to the archived data via NCAR's HPCs?"
    )


    submission_content = forms.ChoiceField(
        choices=SUBMISSION_CONTENT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        label= "Are you submitting a dataset, software, or both?"
    )

    is_ncar_employee = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        label= "Are you an NCAR/UCAR employee?"
    )


class ZenodoChoiceForm(forms.Form):
    continue_with_gdex = forms.ChoiceField(
        choices = YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-control form-control-lg"}),
        label= "Would you still like to submit this dataset to GDEX?"
    )


class BasicInfoForm(forms.Form):
    dataset_title = forms.CharField(
        label='Dataset Title:',
        max_length=500,
        help_text="The complete name used to identify the dataset.",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )

    # Only shown/required when the Advisor was skipped (recommendation
    # submissions) -- normally the Advisor's IntroForm already collected this.
    dataset_size = forms.IntegerField(
        label="Approximate Dataset Size:",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-lg"}),
        help_text="This is an approximation and will be verified later in the process.",
        required=False,
    )

    dataset_size_units = forms.ChoiceField(
        label="Units",
        choices=DATASET_SIZE_UNIT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        required=False,
    )

    dataset_abstract = forms.CharField(
        label="Abstract/Describe Your Data:",
        max_length=5000,
        help_text="A summary highlighting the key characteristics/features of the dataset. "
        "The abstract should be similar to a journal publication abstract in order to provide"
        " sufficient information to inform users if this might be a suitable resource for them.",
        widget=forms.Textarea(attrs={"class": "form-control form-control-lg"}),
    )

    dataset_details = forms.CharField(
        label="Additional Dataset Details:",
        max_length=5000,
        help_text="An extended explanation of the dataset's details, such as background information, "
        "objectives, and methods. The description should provide basic documentation that frames the "
        "context for the dataset. If a more complete description is available in a separate document "
        "format, please indicate the availability of the document in the field. If the document is "
        "accessible via a URL, please provide the URL in the field.",
        widget=forms.Textarea(attrs={"class": "form-control form-control-lg"}),
        required=False,
    )

    def __init__(self, *args, is_recommendation=False, **kwargs):
        super().__init__(*args, **kwargs)
        if is_recommendation:
            self.fields['dataset_size'].required = True
            self.fields['dataset_size_units'].required = True
        else:
            # The Advisor already collected this -- don't ask twice.
            del self.fields['dataset_size']
            del self.fields['dataset_size_units']

        # Django auto-adds a hard HTML `maxlength` for CharFields, which silently truncates
        # typed/pasted text at the limit. Swap it for a data-attribute so the counter can warn
        # the user instead, letting them see (and still submit) the full text they entered.
        for name in ('dataset_title', 'dataset_abstract', 'dataset_details'):
            field = self.fields[name]
            field.widget.attrs['data-maxlength'] = field.max_length
            del field.widget.attrs['maxlength']


class ContributorsMetaForm(forms.Form):
    submitted_by_organization = forms.ChoiceField(
        choices = YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-control form-control-lg"}),
        label= "Is this dataset being submitted by an institution or organization, rather than by a person or people?"
    )


class AuthorForm(forms.Form):
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Doe"}),
    )

    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Jane"}),
    )

    middle_name = forms.CharField(
        label="Middle Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Rose"}),
    )

    orcid_id = forms.CharField(
        label="ORCID iD",
        max_length=19,
        required=False,
        validators=[orcid_validator],
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "0000-0000-0000-0000",}),
    )

    affiliation = forms.CharField(
        label="Institution/Organization",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "NSF National Center for Atmospheric Research (NCAR)"}),
    )

    def __init__(self, *args, is_organization=False, **kwargs):
        self.is_organization = is_organization
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.is_organization:
            if not cleaned_data.get('affiliation'):
                self.add_error('affiliation', "Institution/Organization is required.")
        else:
            if not cleaned_data.get('first_name'):
                self.add_error('first_name', "First name is required.")
            if not cleaned_data.get('last_name'):
                self.add_error('last_name', "Last name is required.")
        return cleaned_data


class _AuthorBaseFormSet(forms.BaseFormSet):
    """Renders the ORDER/DELETE management fields as hidden inputs, driven entirely by JS."""

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_order:
            form.fields['ORDER'].widget = forms.HiddenInput()
        if self.can_delete:
            form.fields['DELETE'].widget = forms.HiddenInput()


AuthorFormSet = forms.formset_factory(
    AuthorForm,
    formset=_AuthorBaseFormSet,
    extra=0,
    can_delete=True,
    can_order=True,
    min_num=1,
    validate_min=True,
)


def _check_location(location):
    """Detects the access method for `location` and, for /glade paths and
    https URLs, verifies it via the check-access service. Returns
    (access_method, verification, error) -- verification is 'readable',
    'reachable', or '' (not applicable/not verified); error is None on
    success or a user-facing message to attach to the offending field.

    The service returns two unrelated response shapes depending on which
    kind of location you give it:
      /glade path: {"globally_readable": bool, "files_scanned": int,
                    "non_readable_files": [...], "truncated": bool}
        -- a real recursive filesystem scan, so `recursive`/`max_results`
        apply.
      https URL:   {"accessible": bool, "status_code": int}
        -- just a plain HTTP reachability check on that exact URL;
        `recursive`/`max_results` are ignored.
    """
    access_method = detect_access_method(location)

    info = ACCESS_METHOD_INFO[access_method]
    if info['pattern'] and not re.match(info['pattern'], location):
        return access_method, '', info['error']

    # The two access methods GDEX can actually verify itself: a /glade path
    # either exists and is readable, or it doesn't/isn't; an https URL either
    # responds or it doesn't. Required, not advisory -- the submitter can't
    # proceed until the check passes.
    if access_method == 'path':
        try:
            result = check_path_access(location)
        except requests.Timeout:
            # A broad, shared parent directory (e.g. a whole collections root
            # spanning many datasets) can take longer to recursively scan
            # than the service itself will wait -- tell the submitter why,
            # rather than a generic "try again" that would just time out
            # identically on retry.
            return access_method, '', (
                "That path is too large to scan directly -- it likely contains many nested "
                "datasets or a very large number of files, and the scan timed out before "
                "finishing. Please provide the specific folder containing just your dataset's "
                "files, rather than a shared parent directory."
            )
        except requests.RequestException:
            # Confirmed via the real service: a nonexistent path comes back
            # as an HTTP error here (e.g. a 404 "Path not found"), not a
            # normal globally_readable=false response -- so this branch
            # specifically means the path itself couldn't be reached at all,
            # not just that some files under it aren't readable.
            return access_method, '', (
                f"Couldn't verify read access on {location} -- this usually means the directory "
                "doesn't exist, or its permissions prevent access entirely. Please check that "
                "path and try again."
            )

        if not result.get('globally_readable'):
            # Deliberately not naming which specific files/directories are
            # unreadable -- with max_results kept low for speed, that list
            # only ever reflects a partial scan anyway. But we do name which
            # of the (up to two) locations this is, since the same generic
            # wording on both fields would be ambiguous.
            return access_method, '', (
                f"Some files under {location} are not readable. Please check permissions on "
                "the files under this directory before continuing."
            )
        return access_method, 'readable', None

    if access_method == 'https':
        try:
            result = check_path_access(location)
        except requests.RequestException:
            return access_method, '', "Couldn't verify that URL right now. Please try again."

        if not result.get('accessible'):
            return access_method, '', (
                f"That URL returned HTTP {result.get('status_code', '???')} and doesn't appear to be "
                "reachable. Please check the URL before continuing."
            )
        # No file count for https -- the service only confirms the URL
        # itself responds, it doesn't recursively scan it.
        return access_method, 'reachable', None

    return access_method, '', None


class AccessInfoForm(forms.Form):
    # No visible access_method field -- it's inferred from dataset_location
    # (see detect_access_method) and stashed into cleaned_data in clean().
    dataset_location = forms.CharField(
        label="Dataset Location",
        help_text="Enter the dataset's HTTPS URL, FTP/SFTP address, S3 URI, absolute /glade path, "
        "or DOI -- we'll detect which one automatically and check it when you click Next.",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )

    # Optional second location -- revealed via "Add another location" in the
    # template. Capped at two: the form only has these two fields, and the
    # template's JS refuses to reveal a third, nudging submitters to
    # consolidate under one parent directory instead.
    dataset_location_2 = forms.CharField(
        label="Additional Dataset Location",
        required=False,
        help_text="If your data doesn't all live under one location, you can add one additional "
        "location here -- we'll detect and check it the same way as above.",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )

    def clean(self):
        cleaned_data = super().clean()

        location = cleaned_data.get('dataset_location')
        if location:
            access_method, verification, error = _check_location(location)
            cleaned_data['access_method'] = access_method
            cleaned_data['access_verification'] = verification
            if error:
                self.add_error('dataset_location', error)

        location_2 = cleaned_data.get('dataset_location_2')
        if location_2:
            access_method_2, verification_2, error_2 = _check_location(location_2)
            cleaned_data['access_method_2'] = access_method_2
            cleaned_data['access_verification_2'] = verification_2
            if error_2:
                self.add_error('dataset_location_2', error_2)

        return cleaned_data


class PoliciesForm(forms.Form):
    def __init__(self, *args, is_ncar_employee=None, **kwargs):
        self.is_ncar_employee = is_ncar_employee
        super().__init__(*args, **kwargs)

    data_policy_agreement = forms.BooleanField(
        required=True,
        label="I agree to the above terms and conditions.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    data_deposit_agreement = forms.BooleanField(
        required=False,
        label="I agree to the data deposit agreement below",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if self.is_ncar_employee == 'False' and not cleaned_data.get('data_deposit_agreement'):
            self.add_error(
                'data_deposit_agreement',
                "Non-UCAR contributors must agree to the Data Deposit Agreement.",
            )
        return cleaned_data

