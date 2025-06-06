"""
WSGI config for gdexwebserver project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
import socket

from django.core.wsgi import get_wsgi_application

hostname = socket.gethostname()
if 'dev' in hostname:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gdexwebserver.settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gdexwebserver.settings.production")

application = get_wsgi_application()
