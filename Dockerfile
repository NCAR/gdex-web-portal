# syntax=docker/dockerfile:1

FROM dattore/gdex-web-portal:web AS intermediate

# set the version number
ARG VERSION_NUMBER=
RUN if [ -z "$VERSION_NUMBER"]; then \
echo "'VERSION_NUMBER' environment variable is missing"; \
exit 1; \
fi
RUN <<EOF
cat <<EOFCAT > /tmp/version_number
$VERSION_NUMBER
EOFCAT
EOF
RUN <<EOF
cat <<EOFCAT > /tmp/get_version_number
#! /bin/bash
cat /usr/local/gdexweb/version_number
EOFCAT
EOF
RUN chmod 755 /tmp/get_version_number

RUN <<EOF
apt-get update -y
apt-get install -y git
mkdir /tmp/gdexweb
git clone https://github.com/NCAR/gdex-web-portal.git /tmp/gdexweb
EOF


FROM dattore/gdex-web-portal:web

# copy from the intermediate
COPY --from=intermediate /tmp/version_number /usr/local/gdexweb/
COPY --from=intermediate /tmp/get_version_number /usr/local/bin/
COPY --from=intermediate /tmp/gdexweb /usr/local/gdexweb

# create the local settings file
RUN \
--mount=type=secret,id=DSSDB_USERNAME,env=DSSDB_USERNAME \
--mount=type=secret,id=DSSDB_PASSWORD,env=DSSDB_PASSWORD \
--mount=type=secret,id=DSSDB_HOST,env=DSSDB_HOST \
--mount=type=secret,id=DSSDB_DBNAME,env=DSSDB_DBNAME \
--mount=type=secret,id=WAGTAIL_USERNAME,env=WAGTAIL_USERNAME \
--mount=type=secret,id=WAGTAIL_PASSWORD,env=WAGTAIL_PASSWORD \
--mount=type=secret,id=WAGTAIL_HOST,env=WAGTAIL_HOST \
--mount=type=secret,id=WAGTAIL_DBNAME,env=WAGTAIL_DBNAME \
--mount=type=secret,id=WAGTAIL_PORT,env=WAGTAIL_PORT \
--mount=type=secret,id=METADATA_USERNAME,env=METADATA_USERNAME \
--mount=type=secret,id=METADATA_PASSWORD,env=METADATA_PASSWORD \
--mount=type=secret,id=METADATA_HOST,env=METADATA_HOST \
--mount=type=secret,id=METADATA_DBNAME,env=METADATA_DBNAME \
--mount=type=secret,id=DJANGO_SUPERUSER_USERNAME,env=DJANGO_SUPERUSER_USERNAME \
--mount=type=secret,id=DJANGO_SUPERUSER_PASSWORD,env=DJANGO_SUPERUSER_PASSWORD \
--mount=type=secret,id=DJANGO_SUPERUSER_EMAIL,env=DJANGO_SUPERUSER_EMAIL \
--mount=type=secret,id=DJANGO_DEV_SECRET,env=DJANGO_DEV_SECRET \
--mount=type=secret,id=DJANGO_PRODUCTION_SECRET,env=DJANGO_PRODUCTION_SECRET \
--mount=type=secret,id=ORCID_AUTH_APP_CLIENT_ID,env=ORCID_AUTH_APP_CLIENT_ID \
--mount=type=secret,id=ORCID_AUTH_APP_SECRET,env=ORCID_AUTH_APP_SECRET \
--mount=type=secret,id=GLOBUS_AUTH_APP_CLIENT_ID,env=GLOBUS_AUTH_APP_CLIENT_ID \
--mount=type=secret,id=GLOBUS_AUTH_APP_SECRET,env=GLOBUS_AUTH_APP_SECRET \
--mount=type=secret,id=GLOBUS_APP_CLIENT_ID,env=GLOBUS_APP_CLIENT_ID \
--mount=type=secret,id=GLOBUS_APP_CLIENT_SECRET,env=GLOBUS_APP_CLIENT_SECRET \
--mount=type=secret,id=GLOBUS_APP_PRIVATE_KEY,env=GLOBUS_APP_PRIVATE_KEY \
--mount=type=secret,id=GLOBUS_TRANSFER_REFRESH_TOKEN,env=GLOBUS_TRANSFER_REFRESH_TOKEN \
--mount=type=secret,id=GLOBUS_AUTH_REFRESH_TOKEN,env=GLOBUS_AUTH_REFRESH_TOKEN \
--mount=type=secret,id=GMAP_API_KEY,env=GMAP_API_KEY \
--mount=type=secret,id=IUSER_COOKIE_ID,env=IUSER_COOKIE_ID \
--mount=type=secret,id=IUSER_COOKIE_CONTENT,env=IUSER_COOKIE_CONTENT \
<<EOF
cat <<EOFCAT > /usr/local/gdexweb/gdexwebserver/settings/local_settings.py
dssdb_config_pg = {
    'user': "$DSSDB_USERNAME",
    'password': "$DSSDB_PASSWORD",
    'host': "$DSSDB_HOST",
    'dbname': "$DSSDB_DBNAME",
}

wagtail2_config_pg = {
    'user': "$WAGTAIL_USERNAME",
    'password': "$WAGTAIL_PASSWORD",
    'host': "$WAGTAIL_HOST",
    'dbname': "$WAGTAIL_DBNAME",
    'port': "$WAGTAIL_PORT",
}

metadata_config_pg = {
    'user': "$METADATA_USERNAME",
    'password': "$METADATA_PASSWORD",
    'host': "$METADATA_HOST",
    'dbname': "$METADATA_DBNAME",
}

IGrML_config_pg = metadata_config_pg

WGrML_config_pg = metadata_config_pg

search_config_pg = metadata_config_pg

DJANGO_SUPERUSER = {
    'username': "$DJANGO_SUPERUSER_USERNAME",
    'email': "$DJANGO_SUPERUSER_EMAIL",
    'password': "$DJANGO_SUPERUSER_PASSWORD",
}

DJANGO_SECRET_KEYS = {
    'dev_secret': "$DJANGO_DEV_SECRET",
    'production_secret': "$DJANGO_PRODUCTION_SECRET",
}

orcid_auth_app = {
    "client_id": "$ORCID_AUTH_APP_CLIENT_ID",
    "secret": "$ORCID_AUTH_APP_SECRET",
    "key": ""
}

globus_auth_app = {
    "client_id": "$GLOBUS_AUTH_APP_CLIENT_ID",
    "secret": "$GLOBUS_AUTH_APP_SECRET",
    "key": ""
}

globus_app_client_id = "$GLOBUS_APP_CLIENT_ID",
globus_app_client_secret = "$GLOBUS_APP_CLIENT_SECRET",
globus_app_private_key = "$GLOBUS_APP_PRIVATE_KEY",
globus_transfer_refresh_token = "$GLOBUS_TRANSFER_REFRESH_TOKEN",
globus_auth_refresh_token = "$GLOBUS_AUTH_REFRESH_TOKEN",

gmap_api_key = "$GMAP_API_KEY"

ICOOKIE = {
    'id': "$IUSER_COOKIE_ID",
    'content': "$IUSER_COOKIE_CONTENT",
}

EOFCAT
EOF

RUN pip install -r /usr/local/gdexweb/requirements.txt
RUN python /usr/local/gdexweb/manage.py collectstatic --noinput

# add aliases for content that apache should serve
RUN <<EOF
cat <<EOFCAT > /etc/apache2/conf-enabled/aliases.conf
Alias /static /usr/local/gdexweb/static
Alias /media /usr/local/gdexweb/media
EOFCAT
EOF

# set permissions
RUN chown -R www-data:www-data /usr/local/gdexweb
RUN chown www-data:www-data /var/log/django.log

# start the web server
ENV PYTHONPATH=/usr/local/gdexweb
CMD ["apache2ctl", "-D", "FOREGROUND"]
