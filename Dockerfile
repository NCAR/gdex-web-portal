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
cat /usr/local/gdexweb/static/version
EOFCAT
EOF
RUN chmod 755 /tmp/get_version_number

RUN apt-get update -y
RUN apt-get install -y git
RUN mkdir /tmp/gdexweb
RUN git clone https://github.com/NCAR/gdex-web-portal.git /tmp/gdexweb


FROM dattore/gdex-web-portal:web

# copy from the intermediate
COPY --from=intermediate /tmp/version_number /usr/local/gdexweb/static/version
COPY --from=intermediate /tmp/get_version_number /usr/local/bin/
COPY --from=intermediate /tmp/gdexweb /usr/local/gdexweb

RUN pip install -r /usr/local/gdexweb/requirements.txt

# set permissions
RUN chown -R www-data:www-data /usr/local/gdexweb
RUN touch /var/log/django.log
RUN chown www-data:www-data /var/log/django.log

RUN <<EOF
cat <<'EOFCAT' > /usr/local/bin/start_container
#! /bin/bash
#
# replace apache2 configuration files from repository
cp -r /usr/local/gdexweb/apache2/* /etc/apache2/
#
# move wsgi.py so that it can be "touched" to clear the django cache
mv /usr/local/gdexweb/gdexwebserver/wsgi.py /data/local/gdexweb/gdexwebserver/
ln -s /data/local/gdexweb/gdexwebserver/wsgi.py /usr/local/gdexweb/gdexwebserver/wsgi.py
#
# link django settings files
mv /usr/local/gdexweb/gdexwebserver/settings/base.py /data/local/gdexweb/gdexwebserver/settings/
ln -s /data/local/gdexweb/gdexwebserver/settings/base.py /usr/local/gdexweb/gdexwebserver/settings/base.py
ln -s /data/local/gdexweb/gdexwebserver/settings/local_settings.py /usr/local/gdexweb/gdexwebserver/settings/local_settings.py
ln -s /data/local/gdexweb/metaman/local_settings.py /usr/local/gdexweb/metaman/local_settings.py
#
# link django apps for testing here
rm -rf /data/test/metaman
mv /usr/local/gdexweb/metaman /data/test/
ln -s /data/test/metaman /usr/local/gdexweb/metaman
rm -rf /data/test/redeploys.py
mv /usr/local/gdexweb/gdexwebserver/redeploys.py /data/test/
ln -s /data/test/redeploys.py /usr/local/gdexweb/gdexwebserver/redeploys.py
#
chown -R www-data:www-data /data
mkdir -p /data/logs/apache2
#
python /usr/local/gdexweb/manage.py collectstatic --noinput
dsspellchecker_manage build_db &
auth_key=`grep doi_manager_auth_key /data/local/gdexweb/metaman/local_settings.py |awk -F\" '{print $2}'`
doi_manage $auth_key configure /data/local/doi_manager/settings.txt
#
/etc/init.d/sendmail start &
#
# start apache
apache2ctl -D FOREGROUND
EOFCAT
EOF
RUN chmod 755 /usr/local/bin/start_container

# start the web server
ENV PYTHONPATH=/usr/local/gdexweb
CMD ["/usr/local/bin/start_container"]
