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

GLOBUS_DATA_ENDPOINT_ID = "c4e40965-a024-43d7-bef4-6010f3731b61"
GLOBUS_REQUEST_ENDPOINT_ID = "e6cd9f43-935c-42e3-8d19-764d03241719"
GLOBUS_S3_ENDPOINT_ID = "558ad782-80dd-4656-a64a-2245f38a7c9e"
GLOBUS_STRATUS_ENDPOINT_ID = GLOBUS_S3_ENDPOINT_ID
GLOBUS_CGD_ENDPOINT_ID = "11651c26-80c2-4dac-a236-7755530731ac"

GLOBUS_RDA_DATA_BASE_PATH = '/glade/campaign/collections/gdex/data/'
GLOBUS_REQUEST_BASE_PATH = '/glade/campaign/collections/gdex/transfer/'

GLOBUS_STRATUS_BASE_PATH = '/rda-data'
GLOBUS_CGD_BASE_PATH = '/glade/campaign/cgd'