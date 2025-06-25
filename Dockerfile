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

RUN apt-get update -y
RUN apt-get install -y git
RUN mkdir /tmp/gdexweb
RUN git clone https://github.com/NCAR/gdex-web-portal.git /tmp/gdexweb


FROM dattore/gdex-web-portal:web

# copy from the intermediate
COPY --from=intermediate /tmp/version_number /usr/local/gdexweb/
COPY --from=intermediate /tmp/get_version_number /usr/local/bin/
COPY --from=intermediate /tmp/gdexweb /usr/local/gdexweb

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
RUN touch /var/log/django.log
RUN chown www-data:www-data /var/log/django.log

RUN <<EOF
cat <<EOFCAT > /usr/local/bin/start_container
#! /bin/bash
chown -R www-data:www-data /data
mkdir -p /data/logs/apache2
cp /usr/local/gdexweb/gdexwebserver/settings/local_settings.py /data/xyz
apache2ctl -D FOREGROUND
EOFCAT
EOF
RUN chmod 755 /usr/local/bin/start_container

# start the web server
ENV PYTHONPATH=/usr/local/gdexweb
CMD ["/usr/local/bin/start_container"]
