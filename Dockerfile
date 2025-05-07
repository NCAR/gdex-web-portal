# syntax=docker/dockerfile:1

FROM dattore/rda-web-test:wagtail AS intermediate

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
cat /usr/local/rdaweb/version_number
EOFCAT
EOF
RUN chmod 755 /tmp/get_version_number

RUN <<EOF
apt-get update -y
apt-get install -y git
mkdir /tmp/rdaweb
git clone https://github.com/rda-dattore/rdaweb.git /tmp/rdaweb
EOF
#ADD git@github.com:rda-dattore/rdaweb.git /tmp/rdaweb


FROM dattore/rda-web-test:wagtail

# copy from the intermediate
COPY --from=intermediate /tmp/version_number /usr/local/rdaweb/
COPY --from=intermediate /tmp/get_version_number /usr/local/bin/
COPY --from=intermediate /tmp/rdaweb /usr/local/rdaweb

# create the local settings file
RUN \
--mount=type=secret,id=WAGTAIL_USERNAME,env=WAGTAIL_USERNAME \
--mount=type=secret,id=WAGTAIL_PASSWORD,env=WAGTAIL_PASSWORD \
--mount=type=secret,id=WAGTAIL_HOST,env=WAGTAIL_HOST \
--mount=type=secret,id=WAGTAIL_DBNAME,env=WAGTAIL_DBNAME \
--mount=type=secret,id=WAGTAIL_PORT,env=WAGTAIL_PORT \
--mount=type=secret,id=DJANGO_SUPERUSER_USERNAME,env=DJANGO_SUPERUSER_USERNAME \
--mount=type=secret,id=DJANGO_SUPERUSER_PASSWORD,env=DJANGO_SUPERUSER_PASSWORD \
--mount=type=secret,id=DJANGO_SUPERUSER_EMAIL,env=DJANGO_SUPERUSER_EMAIL \
<<EOF
cat <<EOFCAT > /usr/local/rdaweb/rdawebserver/settings/local_settings.py
wagtail_config = {
    'user': "$WAGTAIL_USERNAME",
    'password': "$WAGTAIL_PASSWORD",
    'host': "$WAGTAIL_HOST",
    'dbname': "$WAGTAIL_DBNAME",
    'port': "$WAGTAIL_PORT",
}

DJANGO_SUPERUSER = {
    'username': "$DJANGO_SUPERUSER_USERNAME",
    'email': "$DJANGO_SUPERUSER_EMAIL",
    'password': "$DJANGO_SUPERUSER_PASSWORD",
}
EOFCAT
EOF

RUN pip install -r /usr/local/rdaweb/requirements.txt

# create the final setup and run script
RUN <<EOF
cat <<EOFCAT > /usr/local/bin/start_web_server
#! /bin/bash
/usr/local/rdaweb/manage.py makemigrations
/usr/local/rdaweb/manage.py migrate
/usr/local/rdaweb/manage.py collectstatic --noinput
python3.12 /usr/local/rdaweb/manage.py ensuresuperuser
gunicorn --bind 0.0.0.0:443 --workers 4 rdawebserver.wsgi
EOFCAT
EOF
RUN chmod 755 /usr/local/bin/start_web_server

# start gunicorn
ENV PYTHONPATH=/usr/local/rdaweb
CMD ["/usr/local/bin/start_web_server"]
