# content-hub

## Install dependencies
Content Hub depends on jQuery, Django and other Python or java script packages, you must install them before running Content Hub.
Below is the setup commands with the recommended versions of dependencies.

    	dpkg -i python-setuptools_3.3-1ubuntu1_all.deb
    	easy_install --upgrade pip
    	dpkg -i libssl1.0.0_1.0.1f-1ubuntu2.15_amd64.deb
    	dpkg -i libssl-dev_1.0.1f-1ubuntu2.15_amd64.deb
    	dpkg -i libpython2.7-minimal_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i libpython2.7-stdlib_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i libpython2.7_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i libpython2.7-dev_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i libpython-dev_2.7.5-5ubuntu3_amd64.deb
    	dpkg -i python2.7-minimal_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i python2.7_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i python2.7-dev_2.7.6-8ubuntu0.2_amd64.deb
    	dpkg -i libpython-dev_2.7.5-5ubuntu3_amd64.deb
    	dpkg -i python-dev_2.7.5-5ubuntu3_amd64.deb
    	pip install -U Fabric==1.8.2
    	pip install -U django-celery==3.1.16
    	pip install -U celery==3.1.17
    	pip install -U kombu==3.0.24
    	pip install -U amqp==1.4.6
    	pip install -U anyjson==0.3.3
    	pip install -U argparse==1.2.1
    	pip install -U beautifulsoup4==4.3.2
    	pip install -U billiard==3.3.0.19
    	pip install -U django-angular==0.7.5
    	pip install -U six==1.7.3
    	pip install -U django-autocomplete-light==1.4.14
    	pip install -U django-filter==0.7
    	pip install -U django-rest-swagger==0.1.14
    	pip install -U djangorestframework==2.3.14
    	pip install -U django-windows-tools==0.1.1
    	pip install -U Django==1.6.5
    	pip install -U httpretty==0.8.0
    	pip install -U urllib3==1.10.4
    	pip install -U lxml==3.3.6
    	pip install -U mock==1.0.1
    	pip install -U paramiko==1.12.2
    	pip install -U pytz==2014.10
    	pip install -U requests==2.2.1
    	pip install -U South==1.0.2
    	pip install -U wsgiref==0.1.2
    	pip install flup

## Install Content Hub
1.  Copy Content hub source code to the device which is use as Content Hub server.
2.  Remove the old version:

		$ rm -rf /srv/easyconnect/
		$ rm -rf /srv/static/

3.  Install new version:
		
        $ cd Content_Hub_2.0.1/
		$ cp -r /easyconnect/ /srv/
		$ cp -r /static/ /srv/

4.  Add auto-ingestion directory:

		$ mkdir /media/preloaded/auto
		
5.  Add database backup directory:

		$ mkdir /media/preloaded/dbbak

## lighttpd configuration
add corresponding configration in lighttpd.conf as below:

	$SERVER["socket"] == ":80" { 
		server.document-root = "/srv/easyconnect/"
		fastcgi.server = (
	                "/content.fcgi" => (
	                        "main" => (
	                                "socket" => "/tmp/content.sock",
	                                "check-local" => "disable",
	                        )
	                ),
	        )
		alias.url = (
	                "/media" => "/srv/media/",
	                "/static" => "/srv/static/",
	        )
	
	        url.rewrite-once = (
	                "^(/media.*)$" => "$1",
	                "^(/static.*)$" => "$1",
	                "^(/.*)$" => "/content.fcgi$1",
	        )
	}

## LAUNCH CONTENT HUB

1.  Collect the static source and launch Content Hub with the following commands:       
  
 
	cd /srv/easyconnect   
	python manage.py collectstatic   
	python manage.py runfcgi method=prefork   
