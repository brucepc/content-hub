from django.conf import settings as ec_settings
from django.utils import translation
from easyconnect.hw_api import EasyconnectApApi
from contentimport.models import SiteSetting

class SetLanguage(object):
    '''
    Middleware to handle language switching
    '''
    hw_api = EasyconnectApApi()
    current_language = hw_api.get_language_tag()

    def process_request(self, request):
        self.current_language = self.hw_api.get_language_tag()
        if self.current_language is not None:
            translation.activate(self.current_language)
        return None
