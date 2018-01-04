FROM debian:jessie-slim


RUN apt update \
     && apt install -y \
          python2.7 \
          python2.7-dev \
          libssl1.0.0 \
          libssl-dev \
          python-dev \
          python-setuptools \
          lighttpd \
          ca-certificates 
RUN apt install -y build-essential 
RUN apt install -y libxmlsec1-dev libxml2-dev
RUN easy_install pip
RUN mkdir -p /srv
WORKDIR /srv
COPY requirements.txt /srv/
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/lighttpd.conf /srv/lighttpd.conf
COPY easyconnect /srv/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh
RUN mkdir -p /media/preloaded/auto /media/preloaded/dbbak

ENTRYPOINT ["/entrypoint.sh"]
