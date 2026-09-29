import requests

# GDEX's own visualization service -- renders a variable from a NetCDF file
# under /glade with matplotlib and returns the public URL of the PNG.
VISUALIZE_URL = 'https://gdex-services.k8s.ucar.edu/generators/visualize'


def visualize_file(glade_path, variable=None):
    """Returns the service's parsed JSON response for `glade_path`. Raises
    requests.RequestException if the service can't be reached or errors --
    callers decide how to surface that."""
    params = {'path': glade_path}
    if variable:
        params['variable'] = variable
    response = requests.post(VISUALIZE_URL, params=params, timeout=120)
    response.raise_for_status()
    return response.json()
