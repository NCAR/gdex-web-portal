from django.conf import settings
import globus_sdk

def load_app_client():
    """Load the 'NCAR RDA Client' registered at developers.globus.org """

    return globus_sdk.ConfidentialAppAuthClient(settings.GLOBUS_APP_CLIENT_ID, settings.GLOBUS_APP_CLIENT_SECRET)
