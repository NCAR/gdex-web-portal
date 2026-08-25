from django.contrib.auth.models import User


def _is_ucar_staff(self):
    """True if this user's email address is a ucar.edu address.

    Note: this only reflects the email domain, not GDEX/DECS staff
    status (see api.common.get_staff for the latter).
    """
    return bool(self.email) and self.email.lower().endswith('@ucar.edu')


def _get_ucar_username(self):
    """Returns the local part of a ucar.edu email address, e.g.
    'jdoe' for 'jdoe@ucar.edu'. Returns None if the user's email
    isn't a ucar.edu address.
    """
    if not self.is_ucar_staff:
        return None
    return self.email[:-len('@ucar.edu')]


# django.contrib.auth.models.User is used directly throughout this project
# (AUTH_USER_MODEL is not overridden), so there's no local subclass to add
# methods to. Attaching a property/method here is the standard way to
# extend it without a custom user model / migration.
User.add_to_class('is_ucar_staff', property(_is_ucar_staff))
User.add_to_class('get_ucar_username', _get_ucar_username)
