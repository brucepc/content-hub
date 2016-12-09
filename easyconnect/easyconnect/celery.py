from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easyconnect.settings')

app = Celery('easyconnect')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

from celery.task import periodic_task
from celery.schedules import crontab
import os
from distutils.file_util import copy_file
DATABASES = getattr(settings, 'DATABASES', None)
BACKUPDIR = getattr(settings, 'BACKUPDIR', None)

#@app.task(bind=True)
@periodic_task(run_every=crontab(minute="*/1"), ignore_result=True)
def backup_database():
    if os.path.isfile(DATABASES['default']['NAME']):
        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        if not os.path.exists(BACKUPDIR):
            try:
                os.makedirs(BACKUPDIR)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(BACKUPDIR):
            raise IOError("%s exists and is not a directory." % BACKUPDIR)     
    
        dbname = os.path.basename(DATABASES['default']['NAME'])
        backedupDatabase = os.path.join(BACKUPDIR, dbname);
        
        copy_file(src=DATABASES['default']['NAME'], dst=backedupDatabase, update=1)
    return
