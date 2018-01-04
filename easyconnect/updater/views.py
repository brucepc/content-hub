import json
import logging

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
from easyconnect.settings import rtl_languages

from django.utils import translation
from django.views.decorators.cache import never_cache

@never_cache
def updaterhome(request, template='updater/index.html'):
    """
    home tab app
    """
    rtl = check_rtl()

    context = {
        'rtl': rtl,
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
