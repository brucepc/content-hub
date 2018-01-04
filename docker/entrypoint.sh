#!/bin/bash
set -e 
cd /srv;
echo 'yes' | python manage.py collectstatic 
rm -rf /srv/static
cp -r /static /srv/
#python manage.py migrate
python manage.py runfcgi method=prefork socket=/tmp/content.sock daemonize=true umask=000
lighttpd -D -f /srv/lighttpd.conf
