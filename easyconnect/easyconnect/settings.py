"""
Django settings for easyconnect project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

'''updated settings 1.5.*

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']

add alias to apachee to /srv/static
'''


# lighttpd only
FORCE_SCRIPT_NAME = ''

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# Get SECRET_KEY, or generate a new one
try:
    from secret_key import *
except ImportError:
    from django.utils.crypto import get_random_string
    SECRET_DIR = os.path.abspath(os.path.dirname(__file__))
    f = open(os.path.join(SECRET_DIR, 'secret_key.py'), 'w')
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    f.write("SECRET_KEY='" + get_random_string(128, chars) +"'")
    f.close()
    from secret_key import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

#ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ALLOWED_HOSTS = ['*']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    'browse',
    'contentimport',
    'catalogue',
    'djangular',
    'djcelery',
    'updater',
    'hub',
    'teacheradmin',
    'spa',
    'rest_framework',
    'rest_framework_swagger',
    'rest',
    'rest_framework.authtoken',
	'south'
)

import djcelery
djcelery.setup_loader()
CELERY_INCLUDE = ('contentimport.importer',)
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'


# upload progress feedback handler
from django.conf import global_settings 
FILE_UPLOAD_HANDLERS = ('rest.UploadProgressCachedHandler.UploadProgressCachedHandler', ) + \
    global_settings.FILE_UPLOAD_HANDLERS


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'rest.loggingMiddleware.StandardExceptionMiddleware',
    'rest.localizationMiddleware.SetLanguage',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'easyconnect.urls'

WSGI_APPLICATION = 'easyconnect.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/


TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


js_info_dict = {
    'domain': 'djangojs',
    'packages': ('easyconnect',),
}

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

#default language code
LANGUAGE_CODE = 'en_UK'

#comma separated list of language codes which should display right to left
rtl_languages = [
    'ar'
]


SESSION_EXPIRE_AT_BROWSER_CLOSE = True

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates').replace('\\','/'),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages", # 1.6 defaults up to here
    'django.core.context_processors.request', # added to allow access to 'request' in templates
    "easyconnect.context_processors.admin_media_prefix", # Gives us the base admin url
    "easyconnect.context_processors.parent_categories", # Gives us the top-level categories
    "easyconnect.context_processors.battery_status", # Gives us the hardware values
)

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_SERIALIZER_CLASS': 'rest.pagination.CustomPaginationSerializer',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'PAGINATE_BY': 10,
    'PAGINATE_BY_PARAM': 'page_size',
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': ( 
                      'rest_framework.authentication.SessionAuthentication',
                      'rest_framework.authentication.TokenAuthentication',), 
}

SWAGGER_SETTINGS = {
    "exclude_namespaces": [], # List URL namespaces to ignore
    "api_version": '0.1',  # Specify your API's version
    "rest": "/",  # Specify the path to your API not a root level
    "enabled_methods": [  # Specify which methods to enable in Swagger UI
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
    "api_key": '0032149cbf1e1e72c52566a52da1c3b51bf7c41e', # An API key
    "is_authenticated": False,  # Set to True to enforce user authentication,
    "is_superuser": False,  # Set to True to enforce admin only access
}

LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, '../static').replace('\\', '/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static_source"),
    #'/var/www/static/',
)

EC_ROOT = BASE_DIR

USER_ADMIN_NAME   = 'admin'
USER_ADMIN_EMAIL  = 'admin@localhost'
USER_ADMIN_PASSWD = 'admin'
USER_TEACH_NAME   = 'teacher'
USER_TEACH_PASSWD = 'teacher'

MEDIA_ROOT = '/media/' 
MEDIA_URL =  'media/'
#MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
#MEDIA_URL = 'media/'

#BAckup directory for preserving DB
BACKUPDIR = os.path.join(MEDIA_ROOT, 'preloaded', 'dbbak')

#Append to media root if internal HD is full
HDD_DIR = 'ext-cap-hdd/'

# paths for patch operations
'''
PATCH_UPLOAD_DIR = os.path.join(BASE_DIR, 'patch/')
PATCH_UPPER_EXTRACT_DIR = os.path.join(BASE_DIR, 'patch/patch_zip_extract_test/')
PATCH_EXTRACT_DIR = os.path.join(BASE_DIR, 'patch/patch_extract_test/')
PATCH_APPLY_DIR = os.path.join(BASE_DIR, 'patch/patch_apply_test/')
'''

# on device
PATCH_UPLOAD_DIR = '/srv/easyconnect/patch/'
PATCH_UPPER_EXTRACT_DIR = '/srv/easyconnect/patch/patch_zip_extract_test/'
PATCH_EXTRACT_DIR = '/srv/easyconnect/patch/patch_extract_test/'
PATCH_APPLY_DIR = '/srv/'


# absolute path to copy the preloaded content out of
PRELOAD_SOURCE_CONTENT_DIR = os.path.join(MEDIA_ROOT, 'preloaded', 'auto')

# Turn on or off notifications by default
NOTIFICATIONS = True

# Specify the file name used to point to directories
ANCHOR_FILE_NAME = '_ec.anchor'

# appended to MEDIA_ROOT, so no prepended slashes
UPLOAD_CONTENT_DIR = 'uploaded/'
PRELOAD_CONTENT_DIR = 'preloaded/content_dir/'
REMOTE_CONTENT_DIR = 'remote/'

# TODO: need to decide on a permenant location for these
MICROSITE_DIR = PRELOAD_CONTENT_DIR + 'microsites/'
ICONS_DIR = PRELOAD_CONTENT_DIR + '_icon/'

# Default API settings
API_TIMEOUT = 10
API_DEFAULT_URL = "http://127.0.0.1/api/v1/"
API_DEFAULT_RESOURCE_NAME = "contentitem"
# These are optional, set to None if not using
API_DEFAULT_USERNAME = 'test'
API_DEFAULT_KEY = SECRET_KEY
# API_DEFAULT_USERNAME = None
# API_DEFAULT_KEY = None

STORAGE_BUFFER_SIZE_BYTES = 104857600 #100MB

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s --- %(levelname)s --- %(module)s --- ::: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'log_file':{
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'maxBytes': '16777216', # 16megabytes
            'formatter': 'simple'
        },
    },
    'root': {
        'handlers': ['log_file'],
        'level': 'INFO'
    },
}
