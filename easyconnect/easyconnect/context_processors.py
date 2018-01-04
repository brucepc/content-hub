import logging

from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponse

from contentimport.models import Category
from easyconnect.hw_api import EasyconnectApApi

logger = logging.getLogger(__name__)

STATIC_URL = getattr(settings, 'STATIC_URL', None)

def admin_media_prefix(request):
    return {'ADMIN_STATIC_URL': STATIC_URL+"admin/" }

def parent_categories(request):
    p_cats = Category.objects.filter(parent__exact=None)
    return {
        'parent_categories': p_cats
    }

def battery_status(request):
    """
    pull info from hardware api
    """
    response = {'battery': 0, 'internet': 0}

    try:
        hw_api = EasyconnectApApi()
    except Exception as e:
        pass
        #logger.error('Could not access hardware API')
        #logger.exception(e)
    else:
        try:
            battery = hw_api.get_battery_status() # number between 0 and 100, representing remaining battery percentage (i'm assuming)
            if battery:
                response['battery'] = battery
        except Exception as e:
            #logger.error('Could not get battery status')
            #logger.exception(e)
            pass

        try:    
            internet = hw_api.get_internet_mode() # 0, 1, or 2: 0 == internet turned off, 1 == content updates only, 2 == full access
            if internet:
                response['internet'] = internet
        except Exception as e:
            #logger.error('Could not get internet status')
            pass

    return response