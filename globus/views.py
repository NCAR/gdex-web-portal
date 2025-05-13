from django.shortcuts import render, redirect
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.core.validators import validate_email, RegexValidator
from django.urls import reverse
from django.contrib import messages
from django.utils.timezone import now
import difflib
from api.common import get_dataset_location, get_request_info, get_dataset_webhome, format_dataset_id

try:
    from urllib.parse import urlencode, unquote
except:
    from urllib import urlencode, unquote

from .utils import load_app_client
from globus_sdk import (TransferClient, TransferAPIError, GlobusAPIError,
                        TransferData, RefreshTokenAuthorizer)
from globus_sdk.scopes import TransferScopes, AuthScopes

import logging
logger = logging.getLogger(__name__)

import traceback

USER_SCOPES = [
    AuthScopes.openid,
    AuthScopes.email,
    AuthScopes.profile,
    TransferScopes.all
]

#=========================================================================================
def authcallback(request):
    """Handles the interaction with Globus Auth."""

    # If we're coming back from Globus Auth in an error state, the error
    # will be in the "error" query string parameter.
    if 'error' in request.GET:
        context = {
            'data': {
                "Resource": request.path,
                "Error description": request.GET['error'],
                "Occurred at time": now().isoformat()
            }
        }
        return render(request, 'globus/error.html', context)

    # Set up our Globus Auth/OAuth2 state
    this_url = reverse('authcallback-view')
    redirect_uri = request.build_absolute_uri(this_url)
    state = generate_state_parameter(request, settings.GLOBUS_APP_CLIENT_ID, settings.GLOBUS_APP_PRIVATE_KEY)

    scopes = request.session.get('scopes', USER_SCOPES)
    
    logger.debug("[authcallback] redirect_uri: {}".format(redirect_uri))
    logger.info("[authcallback] requested scopes: {}".format(scopes))

    client = load_app_client()
    client.oauth2_start_flow(
        redirect_uri,
        state = state,
        refresh_tokens=True,
        requested_scopes=scopes
    )

    # If there's no "code" query string parameter, we're in this route
    # starting a Globus Auth login flow.
    if 'code' not in request.GET:
        auth_uri = client.oauth2_get_authorize_url()
        logger.debug('[authcallback] auth_uri: {}'.format(auth_uri))
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(str(auth_uri))
        else:
            return redirect(auth_uri)
    else:
        # If we do have a "code" param, we're coming back from Globus Auth
        # and can start the process of exchanging an auth code for a token.
        logger.debug('[authcallback] code received in GET')
        code = request.GET['code']
        logger.debug('[authcallback] code: {}'.format(code))
        try:
            tokens = client.oauth2_exchange_code_for_tokens(code)
            logger.debug('[authcallback] tokens acquired')
        except Exception as e:
            logger.error('[authcallback] Error acquring OAuth tokens')
            logger.error(e)
            logger.error(traceback.format_exc())
            raise 

        if not is_valid_state(request, tokens['state']):
            return HttpResponseForbidden("Invalid state")

        request.session.update({"tokens": tokens.by_resource_server})

        logger.debug("[authcallback] session ID: {}".format(request.session.session_key))

        return transfer(request) 

#=========================================================================================
def save_filelist(request):
    """
    Handles the case where a user creates a custom file list for
    Globus transfer

    - Save user selected files and other form data to the session
    - Redirect to authcallback to begin Globus Auth flow
    """

    logger.debug("request method: {}".format(request.method))

    # Validate POST data
    if request.method == 'POST':
        data = request.POST
        
        if validate_filelist(data):

            logger.debug('Filelist is validated')

            # Save form data to session
            request.session['dsid'] = request.POST['dsid']
            request.session['files'] = request.POST.getlist('files[]') 

            # Start Globus Auth flow 
            return redirect('/globus/authcallback')
        else:
            logger.debug('Filelist is not validated')
            return HttpResponseBadRequest("Invalid request", status=405)
    else:
        return HttpResponseBadRequest("Invalid request", status=405)

#=========================================================================================
def validate_filelist(data):
    """ Validates POST data for curated file lists """

    if 'dsid' not in data:
        return False
    try:
        # Valid dsid = dsnnn.n, nnn.n, or dnnnnnn
        validate_dsid = RegexValidator(r'^((ds)?\d{3}\.\d{1})|(d\d{6})$', 'Invalid dataset ID')
        validate_dsid(data['dsid'])
        logger.debug('dsid validated')
    except ValidationError as e:
        return HttpResponseBadRequest("{}".format(e), status=405)
 
    try:
        files = data.getlist('files[]')
        for i in range(len(files)):
            try:
                validate_file = RegexValidator(r'^([^\s]+)\/([^\/\s]+)$', 'Invalid path/file')
                validate_file(file[i])
            except ValidationError as e:
                return HttpResponseBadRequest("{}".format(e), status=405)
    except:
        logger.debug('files not a list')
        return HttpResponseBadRequest("Files must be in a list", status=405)
        
    return True

#=========================================================================================
def transfer(request):
    """
    - Send user to Globus to select a destination endpoint using the
      Browse Endpoint helper page.
    """
    dsid = request.session['dsid']
    cancelurl = request.build_absolute_uri('/datasets/' + dsid + '/')
    
    logger.debug('[transfer] cancelurl: {}'.format(cancelurl))

    action_url = reverse('submit-transfer-view')

    params = {
    	'method': 'GET',
        'action': request.build_absolute_uri(action_url),
        'filelimit': 0,
        'folderlimit': 1,
        'cancelurl': cancelurl,
        'label': ''
    }

    browse_url = 'helpers/browse-collections'
    browse_endpoint = '{0}{1}?{2}'.format(settings.GLOBUS_APP_URL, browse_url, urlencode(params))
    logger.debug("[transfer] browse_endpoint url: {}".format(browse_endpoint))

    return redirect(browse_endpoint)

#=========================================================================================
def browsecallback(request):
    """ Handles the interaction with the Globus Browse Endpoint
        helper API """

    return submit_transfer(request)

#=========================================================================================
def submit_transfer(request):
    """
    - Take the data returned by the Browse Endpoint helper page
      and make a Globus transfer request.
    - Send the user to the transfer status page with the task id
      from the transfer.
    """

    dsid = request.session['dsid']
    selected = request.session['files']

    logger.debug("[submit_transfer] dsid: {}".format(dsid))
        
    locflag = get_dataset_location(dsid)
    if locflag == 'O':
        source_endpoint_id = settings.GLOBUS_STRATUS_ENDPOINT_ID
    elif locflag == 'C':
        source_endpoint_id = settings.GLOBUS_CGD_ENDPOINT_ID
    else:
        source_endpoint_id = settings.GLOBUS_DATA_ENDPOINT_ID

    if 'endpoint_id' in request.GET:
        destination_endpoint_id = request.GET['endpoint_id']
        request.session['destination_endpoint_id'] = destination_endpoint_id
    else:
        destination_endpoint_id = request.session['endpoint_id']

    if 'path' in request.GET:
        destination_path = request.GET['path']
        request.session['destination_path'] = destination_path
    else:
        destination_path = request.session['destination_path']
    
    """ Instantiate the Globus SDK transfer client """
    tokens = request.session['tokens']['transfer.api.globus.org']
    tc_authorizer = RefreshTokenAuthorizer(tokens['refresh_token'], load_app_client())
    transfer = TransferClient(authorizer=tc_authorizer)

    """ Check if additional consent is required by the user """
    consent_scopes = []
    consent_scopes_source = check_for_consent_required(transfer, source_endpoint_id)
    if consent_scopes_source:
        consent_scopes.extend(consent_scopes_source)
    consent_scopes_dest = check_for_consent_required(transfer, destination_endpoint_id)
    if consent_scopes_dest:
        consent_scopes.extend(consent_scopes_dest)
    if consent_scopes:
        request.session['scopes'] = USER_SCOPES+consent_scopes
        return redirect('/globus/authcallback')

    source_endpoint_display_name = transfer.get_endpoint(source_endpoint_id)['display_name']
    destination_endpoint_display_name = transfer.get_endpoint(destination_endpoint_id)['display_name']

    default_label = "{} to {} transfer".format(source_endpoint_display_name, destination_endpoint_display_name)

    if 'label' in request.GET:
        label = request.GET['label']
        request.session['label'] = label
    else:
        label = request.session['label']
    # label cannot be an empty string.  Check if empty.
    if not label:
        label = default_label

    """ Instantiate TransferData object """
    transfer_data = TransferData(transfer_client=transfer,
                                 source_endpoint=source_endpoint_id,
                                 destination_endpoint=destination_endpoint_id,
                                 label=label)

    """ Add files to be transferred.  Note source_path is relative to the source
        endpoint base path. """
    for file in selected:
        logger.debug('[submit_transfer] file: {}'.format(file))

        # trim leading '/data/' or '/data/OS/' from path if present.  Trim whitespace at ends.
        if (source_endpoint_id == settings.GLOBUS_STRATUS_ENDPOINT_ID and file.find('/data/OS/',0,9) == 0):
            file = file.replace('/data/OS/','',1).strip()
        elif (source_endpoint_id == settings.GLOBUS_DATA_ENDPOINT_ID and file.find('/data/',0,6) == 0):
            file = file.replace('/data/','',1).strip()
        
        if source_endpoint_id == settings.GLOBUS_CGD_ENDPOINT_ID:
            source_path = get_guest_collection_file_path(dsid, file)
        else:
            source_path = file

        dest_path = destination_path + file
        logger.debug('[submit_transfer] source_path: {}'.format(source_path))
        logger.debug('[submit_transfer] dest_path: {}'.format(dest_path))
        transfer_data.add_item(source_path, dest_path)

    # endpoint_autoactivate is deprecated with GCSv5
    # transfer.endpoint_autoactivate(source_endpoint_id)
    # transfer.endpoint_autoactivate(destination_endpoint_id)
    
    try:
        transfer_result = transfer.submit_transfer(transfer_data)
        task_id = transfer_result['task_id']
        msg = ("transfer code: {0}, "
               "submission_id: {1}, "
               "task_id: {2}, "
               "request_id: {3}, "
               "message: {4}, "
               "dsid: {5}").format(transfer_result['code'], 
                                               transfer_result['submission_id'], 
                                               transfer_result['task_id'], 
                                               transfer_result['request_id'], 
                                               transfer_result['message'], 
                                               dsid)
        logger.info(msg)
    except GlobusAPIError as e:
        context = {
            'data': {
                'Resource': request.path,
                'HTTP status': e.http_status,
                'Error code': e.code,
                'Error message': e.message,
                'Occurred at time': now().isoformat()
            }
        }
        msg = ("Globus API Error:\n"
            "HTTP status: {0}\n"
            "Error code: {1}\n"
            "Error message: {2}\n"
            "dsid: {3}\n"
            "source endpoint: {4}\n"
            "destination endpoint: {5}".format(e.http_status, e.code, e.message, dsid, source_endpoint_id, destination_endpoint_id)
        )
        if e.info.consent_required:
            msg += "\nConsentRequired error with scopes: {}".format(e.info.consent_required.required_scopes)
        logger.error(msg)
        return render(request, 'globus/error.html', context)

    messages.info(request, 'Transfer request submitted successfully.  Task ID: {}'.format(task_id))

    status_url = reverse('status-view', kwargs={'task_id': task_id})
    logger.debug('[submit_transfer] status_url: {}'.format(status_url))

    return redirect(status_url)

#=========================================================================================
def transfer_status(request, task_id):
    """
    Call Globus Transfer API to get status/details of transfer with
    task_id.  The target template (tranfer_status.html) expects a 
    Transfer API 'task' object.
    'task_id' is passed to the route in the URL as 'task_id'.
    """

    transfer_tokens = request.session['tokens']['transfer.api.globus.org']

    authorizer = RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        load_app_client(),
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'])

    transfer = TransferClient(authorizer=authorizer)
    task = transfer.get_task(task_id)
    task_data = task.data
    task_data.update({'dsid': request.session['dsid']})

    logger.debug('[transfer_status] task_id: {}'.format(task_id))
    logger.debug('[transfer_status] task_id from task document: {}'.format(task_data['task_id']))

    return render(request, 'globus/status.html', context=task_data)

#=========================================================================================
def get_guest_collection_url(dsid=None, locflag=None, rindex=None):
    """ Returns the URL for the guest collection endpoint in the Globus File Manager.
        Either dataset ID (dsid) or request index (rindex) is required.  If neither
	dsid or rindex are provided, the default URL returned is the top level URL for 
	the 'NCAR RDA Dataset Archive' guest collection.
	
	Optional argument locflag = location flag of dataset ('G' = glade, 'O' = stratus, 
	'B' = both glade and stratus, 'C' = CGD data under /glade/campaign/cgd/cesm)
    """

    globus_url = settings.GLOBUS_FILE_MANAGER_URL

    if rindex:
        origin_id = settings.GLOBUS_REQUEST_ENDPOINT_ID
        try:
            rqst_info = get_request_info(rindex)
        except:
            msg = "[get_guest_collection_url] Problem getting info for request index {}".format(rindex)
            logger.error(msg)

        if rqst_info['location']:
            base_path = settings.RDA_DATA_REQUEST_PATH
            loc = rqst_info['location']
            loc = loc.rstrip("/")
            if (loc.find(base_path) != -1):
                path_len = len(base_path)
                origin_path = "/{0}/".format(loc[path_len:])
            else:
                origin_path = None
        else:
            origin_path = "/download.auto/{0}/".format(rqst_info['request_id'])

    elif dsid:
        logger.debug("locflag: {}".format(locflag))
        if not locflag:
            locflag = get_dataset_location(dsid)
        if locflag == 'C':
            origin_id = settings.GLOBUS_CGD_ENDPOINT_ID
        elif locflag == 'O' or locflag == 'B':
            origin_id = settings.GLOBUS_STRATUS_ENDPOINT_ID
        else:
            origin_id = settings.GLOBUS_DATA_ENDPOINT_ID
        origin_path = get_guest_collection_origin_path(dsid)
    else:
        origin_id = settings.GLOBUS_DATA_ENDPOINT_ID
        origin_path = "/"
	
    params = {'origin_id': origin_id, 'origin_path': origin_path}
    url = '{0}?{1}'.format(globus_url, urlencode(params))

    return url

#=========================================================================================
def get_guest_collection_origin_path(dsid):
    """ Get the relative path on a guest collection for a dataset """

    webhome = get_dataset_webhome(dsid)
    locflag = get_dataset_location(dsid)

    if locflag == 'C':
        gc_base_path = settings.GLOBUS_CGD_BASE_PATH
        origin_path = webhome.replace(gc_base_path, '', 1)
    else:
        origin_path = "/{}/".format(dsid)

    return origin_path

#=========================================================================================
def get_guest_collection_file_path(origin_path, wfile):
    """ Get path to wfile on CGD or other non-standard guest collections.
        Return value is relative to the Globus guest collection origin
        path. 
    """

    # trim leading and trailing '/' from origin_path and wfile if necessary
    origin_path = origin_path.strip('/')
    wfile = wfile.strip('/')

    # check for overlap between origin_path and wfile
    s = difflib.SequenceMatcher(None, origin_path, wfile)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'insert':
            return origin_path + wfile[j1:]   
    return os.path.join(origin_path, wfile)

#=========================================================================================
def generate_state_parameter(request, client_id, private_key):
    """ Generate a state parameter for OAuth2 requests """

    import hmac
    from base64 import b64encode
    import hashlib

    if not request.session.session_key:
        request.session.create()
    sid = request.session.session_key
    raw_state = sid + client_id

    """ Note hmac requires bytearrays in Python 3. Convert strings to bytes via encode(). """
    hashed = hmac.new(private_key.encode(), raw_state.encode(), hashlib.sha1)
    state = b64encode(hashed.digest())

    """ Convert result back to string """
    decoded_state = state.decode()
    request.session['state'] = decoded_state

    return decoded_state

#=========================================================================================
def is_valid_state(request, state):
    """ Validate the OAuth2 state parameter """
    if state == request.session['state']:
        logger.debug("[is_valid_state] state validated")
        return True
    else:
        logger.debug("[is_valid_state] state not validated")
        return False

#=========================================================================================
def check_for_consent_required(transfer_client, target):
    """ Catch any ConsentRequired errors 
        Reference: https://globus-sdk-python.readthedocs.io/en/stable/examples/minimal_transfer_script/index.html#best-effort-proactive-handling-of-consentrequired
    """
    consent_required_scopes = []
    try:
        transfer_client.operation_ls(target, path='/')
    except TransferAPIError as err:
        if err.info.consent_required:
            consent_required_scopes.extend(err.info.consent_required.required_scopes)
            msg = ("Transfer API Error:\n"
                   "HTTP status: {0}\n"
                   "Error code: {1}\n"
                   "Error message: {2}\n"
                   "endpoint: {3}".format(err.http_status, err.code, err.message, target)
            )
            msg += "\nConsentRequired error with scopes: {}\nRedirecting user to provide consent.".format(err.info.consent_required.required_scopes)
            logger.error(msg)

    return consent_required_scopes
