import re

import requests
from django import forms

from ..services import check_path_access

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
