import os
from django.conf import settings
from django.core import management
from contentimport.models import SiteSetting
import distutils.core

import logging
logger = logging.getLogger(__name__)

DATABASES = getattr(settings, 'DATABASES', None)
MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', None)
UPLOAD_CONTENT_DIR = getattr(settings, 'UPLOAD_CONTENT_DIR', None)
REMOTE_CONTENT_DIR = getattr(settings, 'REMOTE_CONTENT_DIR', None)
PRELOAD_CONTENT_DIR = getattr(settings, 'PRELOAD_CONTENT_DIR', None)
PRELOAD_SOURCE_CONTENT_DIR = getattr(settings, 'PRELOAD_SOURCE_CONTENT_DIR', None)
NOTIFICATIONS = getattr(settings, 'NOTIFICATIONS', True)

'''
API_DEFAULT_URL = getattr(settings, 'API_DEFAULT_URL', None)
API_DEFAULT_USERNAME = getattr(settings, 'API_DEFAULT_USERNAME', None)
API_DEFAULT_KEY = getattr(settings, 'API_DEFAULT_KEY', None)
API_DEFAULT_RESOURCE_NAME = getattr(settings, 'API_DEFAULT_RESOURCE_NAME', None)
'''

def db_table_exists(table, cursor=None):
    try:
        if not cursor:
            from django.db import connection
            cursor = connection.cursor()
        if not cursor:
            raise Exception
        table_names = connection.introspection.get_table_list(cursor)
    except:
        return false
    else:
        return table in table_names

def init_database():
    #initial check for database, if there, check it was successfully set up
    dbcomplete = False
    if os.path.isfile(DATABASES['default']['NAME']):
        logger.info('Database exists, checking if startup completed last time')
        try:
            if SiteSetting.objects.filter(name="dbcomplete").exists():
                logger.info('__dbcomplete entry exists')
                dbcomplete = SiteSetting.objects.get(name="dbcomplete").value
            else:
                logger.info('__dbcomplete entry does not exist')
            #if database exists but not complete, delete it
            if not dbcomplete == 'True':
                logger.info('Database incomplete, deleting...')
                management.call_command('flush', verbosity=0, interactive=False)
        except:
            logger.info('__database exists but is corrupt, rebuilding')
            pass
    
    # create database if non existant
    if not dbcomplete == 'True':
        from django.core.files.storage import FileSystemStorage
        from contentimport.importer import Importer
        from contentimport.lib import generate_tag_scores
        from contentimport.models import RemoteAPI, Tag, Category

        logger.info("Database not found; Startup sequence initiated")

        # Copy preloaded content from source
        preload_source = PRELOAD_SOURCE_CONTENT_DIR
        try:
            distutils.dir_util.remove_tree(MEDIA_ROOT + PRELOAD_CONTENT_DIR)
        except OSError:
            logger.warn("Could not delete content dir")

        try:
            distutils.dir_util.copy_tree(PRELOAD_SOURCE_CONTENT_DIR, MEDIA_ROOT + PRELOAD_CONTENT_DIR)
        except OSError:
            logger.warn("Preload directory tree creation error")

        # Create the database and collect static files
        management.call_command('syncdb', verbosity=0, interactive=False)
        management.call_command('migrate', 'rest_framework.authtoken', verbosity=0, interactive=False)
        management.call_command('migrate', 'djcelery', verbosity=0, interactive=False)
        management.call_command('migrate', 'contentimport', verbosity=0, interactive=False)
        
        management.call_command('collectstatic', verbosity=0, interactive=False)

   
        # os.chdir(EC_ROOT)
        # os.system('python manage.py migrate contentimport')

    
        # Add settings to the database
        logger.info("Importing default settings")
        try:
            notification_setting = SiteSetting.objects.create(name="notifications", value=NOTIFICATIONS)
        except:
            notification_setting = SiteSetting.objects.create(name="notifications", value="False")

        # Import the preloaded content into the db
        preload_directory = MEDIA_ROOT + PRELOAD_CONTENT_DIR
        logger.info("Trying to import preload files from " + preload_directory)

        fs = FileSystemStorage(location=preload_directory)
        dir_list, file_list = fs.listdir(preload_directory)
        everything_list = dir_list + file_list
        logger.info("Content Items found: " + str(everything_list))

        ignore_list = ['lost+found']
        for x in everything_list:
            if any(x in ig for ig in ignore_list):
                logger.info('ignoring directory:' + x)
            else:
                try:
                    logger.info("Importer: " + preload_directory + x)
                    Importer(preload_directory + x, is_preloaded=True)
                except:
                    logger.warn('Corrupt file encountered in preload proccess, contact support!')
                    pass

        logger.info('Import complete')
    
        # All tags and categories so far are preloaded, so...
        Tag.objects.all().update(locked=True)
        Category.objects.all().update(locked=True)


        # Update search, generate tag cloud, add to log
        generate_tag_scores()

        dbcomplete, created = SiteSetting.objects.get_or_create(name="dbcomplete", defaults={'value':True})
        if not created:
            logger.info('___not created')
            dbcomplete.value = True
            dbcomplete.save()
        else:
            logger.info('___created')

    # database exists and is complete, try migration
    else:
        pass
        
        if not db_table_exists('south_migrationhistory'):
            management.call_command('syncdb', verbosity=0, interactive=False)
            management.call_command('migrate', 'contentimport', '0001', fake=True, verbosity=1, interactive=False)
        else:
            management.call_command('syncdb', verbosity=0, interactive=False)
        try:
            management.call_command('migrate', 'contentimport', verbosity=1, interactive=False)
        except:
            management.call_command('migrate', 'contentimport', verbosity=1, interactive=False)

        management.call_command('collectstatic', verbosity=0, interactive=False)

