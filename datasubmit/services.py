import requests

# GDEX's own file-access-check service -- confirms a /glade path or an
# https URL actually exists and is readable (recursively) before staff try
# to archive from it.
CHECK_ACCESS_URL = 'https://gdex-services.k8s.ucar.edu/files/check-access'
# This is how many files the SERVICE scans before giving up and returning
# truncated=True. Kept low deliberately, for speed -- the error message no
# longer reports a file count or which files/directories are unreadable
# (see AccessInfoForm.clean()), so there's no accuracy benefit to scanning
# further once we already know the path has a permissions problem.
CHECK_ACCESS_MAX_RESULTS = 10


def check_path_access(location):
    """Returns the service's parsed JSON dict for `location` (a /glade path
    or an https URL). Raises requests.RequestException if the service itself
    can't be reached -- callers decide how to surface that."""
    response = requests.get(
        CHECK_ACCESS_URL,
        params={'path': location, 'recursive': 'true', 'max_results': CHECK_ACCESS_MAX_RESULTS},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
