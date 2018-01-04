"""
WSGI config for easyconnect project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "easyconnect.settings")

##### Custom startup code goes here
import time
timing_now = time.clock()

from django.conf import settings
from easyconnect.startup_branding import get_branding
from easyconnect.startup_database import init_database
from easyconnect.startup_user_accounts import update_teacher_account, update_admin_account
from easyconnect.startup_additional import begin, finalize
from easyconnect.database_maintenance import restore_database, backup_database

import logging
logger = logging.getLogger(__name__)
logger.info('Starting CH Boot Sequence...')
DATABASES = getattr(settings, 'DATABASES', None)

# stub method to allow future startup processes to be added
begin()
# initialize the custom branding if available
get_branding()

# check for existing database or create new
try:
    init_database()
except Exception as ex:
    from django import db
    db.close_connection()
    if os.path.isfile(DATABASES['default']['NAME']):
        os.remove(DATABASES['default']['NAME'])

    restore_database(os.path.basename(DATABASES['default']['NAME']))    
    init_database()

# Start database backup code after database has been initialized
backup_database()

# initialize or update the accounts from the HW_API
update_teacher_account()
update_admin_account()
# stub method to allow future startup processes to be added
finalize()

startup_time = time.clock() - timing_now
logger.info('Startup completed in: ' + str(startup_time) + ' seconds')
##### Custom startup code ends here

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
