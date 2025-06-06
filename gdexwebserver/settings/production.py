from .base import *
from . import local_settings # noqa

DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = local_settings.DJANGO_SECRET_KEYS['production_secret']

ALLOWED_HOSTS = [".ucar.edu", "localhost", "127.0.0.1"]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ADMINS = [('Riley', 'rpconroy@ucar.edu'),]

try:
    from .local import *
except ImportError:
    pass
