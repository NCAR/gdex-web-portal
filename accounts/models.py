import logging

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

logger = logging.getLogger(__name__)

# How long to trust a SAM lookup result / a SAM lookup failure before
# re-checking. The failure TTL is kept short so a SAM outage doesn't
# get "stuck" for a user whose account status changes, but still keeps
# a down API from being hit on every single property access.
SAM_HPC_ACCOUNT_CACHE_TTL = 60 * 60  # 1 hour
SAM_HPC_ACCOUNT_ERROR_CACHE_TTL = 60  # 1 minute


def _is_ucar_email(email):
    return bool(email) and email.lower().endswith('@ucar.edu')


def _ucar_username_from_email(email):
    """Returns the local part of a ucar.edu email address, e.g.
    'jdoe' for 'jdoe@ucar.edu'. Returns None if the address isn't a
    ucar.edu address.
    """
    if not _is_ucar_email(email):
        return None
    return email[:-len('@ucar.edu')]


def _find_sam_username(email):
    """Looks up email in SAM's autocomplete endpoint
    (/api/v1/users/search) and returns the username of the exact
    email match, or None if there isn't one.

    Used for accounts that aren't @ucar.edu addresses (e.g. external
    collaborators with SAM/HPC access), where the username can't be
    derived from the email address itself.
    """
    response = requests.get(
        f'{settings.SAM_API_BASE_URL}/api/v1/users/search',
        params={'q': email, 'limit': 5},
        auth=(settings.SAM_API_USER, settings.SAM_API_KEY),
        timeout=5,
    )
    response.raise_for_status()
    for row in response.json():
        if row.get('email', '').lower() == email.lower():
            return row.get('username')
    return None


def _has_hpc_account(self):
    """True if this user has an active SAM/HPC account
    (sam.hpc.ucar.edu), regardless of NCAR/UCAR affiliation -- this
    covers external collaborators (e.g. an @ci.uchicago.edu address)
    with HPC access just as much as NCAR staff.

    Resolves this user to a SAM username -- directly from the local
    part of the address for a ucar.edu email, otherwise via a SAM
    email search -- then looks that user up in SAM and considers them
    an HPC-account holder if the account exists and is active. (SAM's
    'organizations' field isn't used: external accounts can be active
    with no organization affiliation at all.) The result is cached per
    email for SAM_HPC_ACCOUNT_CACHE_TTL seconds.

    If SAM can't be reached (or errors), this fails closed to False --
    there's no reliable signal (e.g. email domain) to substitute for
    "has a SAM account" -- and caches that failure for only
    SAM_HPC_ACCOUNT_ERROR_CACHE_TTL seconds so a SAM outage doesn't
    get "stuck".
    """
    email = self.email
    if not email:
        return False

    cache_key = f'sam_has_hpc_account:{email.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        username = (
            _ucar_username_from_email(email) if _is_ucar_email(email)
            else _find_sam_username(email)
        )
        if not username:
            result = False
        else:
            response = requests.get(
                f'{settings.SAM_API_BASE_URL}/api/v1/users/{username}',
                auth=(settings.SAM_API_USER, settings.SAM_API_KEY),
                timeout=5,
            )
            if response.status_code == 404:
                result = False
            else:
                response.raise_for_status()
                data = response.json()
                result = bool(data.get('active'))
        cache.set(cache_key, result, SAM_HPC_ACCOUNT_CACHE_TTL)
        return result
    except (requests.RequestException, ValueError):
        # ValueError covers a non-JSON response.
        logger.warning("SAM HPC-account lookup failed for %s", email, exc_info=True)
        cache.set(cache_key, False, SAM_HPC_ACCOUNT_ERROR_CACHE_TTL)
        return False


def _get_hpc_username(self):
    """Returns this user's SAM/HPC username, or None if it can't be
    determined. For a ucar.edu email it's the local part of the address;
    otherwise it's looked up in SAM by email (cached for
    SAM_HPC_ACCOUNT_CACHE_TTL seconds). Does not check that the account
    is active -- see has_hpc_account for that.
    """
    email = self.email
    if not email:
        return None
    if _is_ucar_email(email):
        return _ucar_username_from_email(email)

    cache_key = f'sam_hpc_username:{email.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached or None

    try:
        username = _find_sam_username(email)
    except (requests.RequestException, ValueError):
        logger.warning("SAM username lookup failed for %s", email, exc_info=True)
        cache.set(cache_key, '', SAM_HPC_ACCOUNT_ERROR_CACHE_TTL)
        return None
    # '' is cached for "no match" since cache.get() can't tell None from a miss.
    cache.set(cache_key, username or '', SAM_HPC_ACCOUNT_CACHE_TTL)
    return username


def _get_ucar_username(self):
    """Returns the local part of a ucar.edu email address, e.g.
    'jdoe' for 'jdoe@ucar.edu'. Returns None if the user's email
    isn't a ucar.edu address.
    """
    return _ucar_username_from_email(self.email)


# django.contrib.auth.models.User is used directly throughout this project
# (AUTH_USER_MODEL is not overridden), so there's no local subclass to add
# methods to. Attaching a property/method here is the standard way to
# extend it without a custom user model / migration.
User.add_to_class('has_hpc_account', property(_has_hpc_account))
User.add_to_class('hpc_username', property(_get_hpc_username))
User.add_to_class('get_ucar_username', _get_ucar_username)
