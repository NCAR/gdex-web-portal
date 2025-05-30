'''
Globus app settings
'''

from . import local_settings

GLOBUS_APP_URL = 'https://app.globus.org/'
GLOBUS_FILE_MANAGER_URL = 'https://app.globus.org/file-manager'
GLOBUS_REDIRECT_URI = '/globus/authcallback/'

GLOBUS_APP_CLIENT_ID = local_settings.globus_app_client_id
GLOBUS_APP_CLIENT_SECRET = local_settings.globus_app_client_secret
GLOBUS_APP_PRIVATE_KEY = local_settings.globus_app_private_key
GLOBUS_APP_TRANSFER_REFRESH_TOKEN = local_settings.globus_transfer_refresh_token
GLOBUS_APP_AUTH_REFRESH_TOKEN = local_settings.globus_auth_refresh_token

GLOBUS_DATA_ENDPOINT_ID = "b6b5d5e8-eb14-4f6b-8928-c02429d67998"
GLOBUS_STRATUS_ENDPOINT_ID = "be4aa6a8-9e35-11eb-8a8e-d70d98a40c8d"
GLOBUS_REQUEST_ENDPOINT_ID = "e1e2997e-d794-4868-838e-d4b8d5590853"
GLOBUS_CGD_ENDPOINT_ID = "11651c26-80c2-4dac-a236-7755530731ac"

GLOBUS_DATA_DOMAIN = 'data.rda.ucar.edu'
GLOBUS_STRATUS_DOMAIN = 'stratus.rda.ucar.edu'
GLOBUS_REQUEST_DOMAIN = 'request.rda.ucar.edu'
CGD_HTTPS_DOMAIN = 'g-09c647.7a577b.6fbd.data.globus.org'

GLOBUS_RDA_DATA_BASE_PATH = '/glade/campaign/collections/rda/data/'
GLOBUS_REQUEST_BASE_PATH = '/glade/campaign/collections/rda/transfer/'
GLOBUS_STRATUS_BASE_PATH = '/rda-data'
GLOBUS_CGD_BASE_PATH = '/glade/campaign/cgd'