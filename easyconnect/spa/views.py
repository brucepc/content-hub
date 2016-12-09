import json
import logging
import json

from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404, render_to_response, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse, Http404
from django.utils.html import escape
from django.forms.models import modelform_factory
from django.db.models.loading import get_models, get_app, get_apps
from django.views.generic import ListView, DetailView
from django.core import serializers
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView, DeleteView
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.conf import settings as ec_settings
#from easyconnect import settings as ec_settings
from easyconnect.settings import rtl_languages, BASE_DIR

from contentimport.models import ContentItem, Category, Tag, TeacherGroup, TeacherGroupMembership, Log, Notify, SiteSetting, Tile
from contentimport.forms import UploadForm
from contentimport.lib import upload_handler, category_dictionary

from catalogue.forms import GroupItems

from django.utils import translation
import os

from django.shortcuts import redirect
from django.core.urlresolvers import resolve

from random import randint

from hub.views import hubhome
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache

class Test(APIView):
    Authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        '''
        handler to check user state and dispatch the appropriate view
        '''
        '''
        tiles_visible_to_all = Tile.objects.filter(visible=True)
        tiles_visible_to_teacher = Tile.objects.filter(teacher_only=True, visible=True)
        
        if (tiles_visible_to_all.count() > 0):
            return hubhome(request, *args, **kwargs)
        else:
            return spahome(request, *args, **kwargs)
        '''
        return spahome(request, *args, **kwargs)

@never_cache
def spahome(request, template='index.html'):
    """
    home tab showing featured lessons and items
    """
    rtl = check_rtl()
    hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})
    context = {
        'libhidden' : hide_lib_setting.value,
        'rtl': rtl
        #'current_language': current_language,
    }

    return render_to_response(template, context, context_instance=RequestContext(request))

def check_rtl():
    return translation.get_language() in rtl_languages

from django.template import Context, Template
def handler404(request):
    template = loader.get_template('404page.html')
    context = Context({
        'message': 'All: %s' % request,
        })
    return HttpResponse(content=template.render(context), content_type='text/html; charset=utf-8', status=404)

from django.views.generic import TemplateView as Django_TemplateView
from easyconnect.hw_api import EasyconnectApApi
class TemplateViewTrans(Django_TemplateView):
    """
    Override TemplateView to pass rtl variable to standalone partials/view (i.e. help pages)
    This is called directly via the urls.py
    """
    help_type = 'teacher' #'teacher' or 'student'

    def get_context_data(self, **kwargs):
        context = super(TemplateViewTrans, self).get_context_data(**kwargs)
        #uncomment when translated help pages become available
        context.update({'rtl': check_rtl()})
        hw_api = EasyconnectApApi()
        current_language = hw_api.get_language_tag()
        view_root = 'helpfiles/eng_UK/'
        suffix = 'help.html' if self.help_type == 'teacher' else 'admin_help.html' if self.help_type == 'admin' else 'student_help.html'
        if current_language:
            view_root = 'helpfiles/' + current_language + '/'
        view_root = view_root + suffix

        if not os.path.isfile(os.path.join(BASE_DIR, 'spa', 'templates', view_root)):
            view_root = 'views/help.html' #temp default

        self.template_name = view_root
        return context

'''
def glorifiedusbstick(request):
    #debug for dev on local device
    abs_path = os.path.dirname(os.path.dirname(__file__)) + '/media/classconnect_drive/'

    root = '/glorifiedusbstick/'
    dir_to_list = request.path.replace(root, abs_path, 1)
    dir = os.listdir(dir_to_list)

    parent = ''
    if dir_to_list == abs_path:
        parent = None
    else:
        parent = os.path.dirname(dir_to_list)
        parent = os.path.dirname(parent) + '/'
        parent = parent.replace(abs_path, root, 1)
    listing = []

    #iterate once for directories
    for name in dir:
        if os.path.isdir(dir_to_list + name):
            href = request.path + name + '/'
            listing.append({
                'type': 'd',
                'link': href,
                'name': name
            })
    #the again so files appear at bottom of list
    for name in dir:
        if not os.path.isdir(dir_to_list + name):
            listing.append({
                'type': 'f',
                'link': None,
                'name': name
            })

    return render_to_response('directory.html', { 'listing': listing, 'parent': parent }, context_instance=RequestContext(request))
'''
