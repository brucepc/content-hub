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
from django.db.models.signals import post_save, pre_save, post_delete
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.conf import settings

from contentimport.models import ContentItem, Category, Tag, TeacherGroup, TeacherGroupMembership, Log, Notify, SiteSetting
from contentimport.forms import UploadForm
from contentimport.lib import upload_handler, category_dictionary

from catalogue.forms import GroupItems

from easyconnect.hw_api import EasyconnectApApi

RESULTS_PER_PAGE = getattr(settings, 'HAYSTACK_SEARCH_RESULTS_PER_PAGE', 10)
TAG_CLOUD_MAX = 10

logger = logging.getLogger(__name__)

@login_required
def lesson_json(request):
    desired_id = request.GET.get('id', None)
    lesson_items = ContentItem.objects.exclude(hidden=True)

    if desired_id is not None:
        lesson_items = lesson_items.filter(teachergroup__pk=desired_id)

    json_models = serializers.serialize("json", lesson_items)

    return HttpResponse(json_models, content_type='application/json')

def category_children_json(request):
    parent_id = request.GET.get('parent', None)
    ## None means no parent, do we need the context at all??
    children = Category.objects.filter(parent__exact=parent_id)

    json_models = serializers.serialize("json", children)

    return HttpResponse(json_models, content_type='application/json')

def filter_view(request, source=None, template='browse/library.html'):

    # Redirect logged in user to /preloaded/ by default if they try to go to just /library/
    #if request.user.is_authenticated() and source is None:
    #    return HttpResponseRedirect(reverse('library', kwargs={'source': 'preloaded'}))

    #if user is not logged in and tries /library when it is hidden: redirect to home
    hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})
    if 'library.html' in template:
        if request.user.is_authenticated() == False:
            if hide_lib_setting.value == "True":
                #Not teacher & library is hidden return to home
                return HttpResponseRedirect("/")
        else:
            if hide_lib_setting == "True" and request.session['viewType'] == "student":
                return HttpResponseRedirect("/")

    legit_sources = ['preloaded', 'uploaded']
    if source is not None:
        if source not in legit_sources:
            raise Http404("Sorry, no results on that page.")

    # Pull fields from the GET
    model = request.GET.get('m', 0) # 0 is for library, 1 for lessons
    query = request.GET.get('q', None)
    category = request.GET.get('c', None) # only the 'bottom' category will be needed, for now
    tags = request.GET.getlist('t', None)

    if 'lessons.html' in template:
        model = TeacherGroup
    else:
        model = ContentItem
    
    sort_by = request.GET.get('sort_by', 'date')
    #date : date_added
    #name : title
    sort_by_modelname = 'title' if sort_by == 'name' else 'date_added'

    #if user is student library should display both preloaded and uploaded content together.
    if request.user.is_authenticated() == False or request.session['viewType'] == "student":
        source = 'both'
        exclude_hidden = True
    else:
        exclude_hidden = False

    #is_teacher = request.user.is_authenticated()
    #if is_teacher:
    #    exclude_hidden = request.session['viewType'] == "student" #if teacher and viewed as student

    paginator = get_results(model, source, query, category, tags, exclude_hidden, sort_by_modelname)
    paginator.sort_method = sort_by
    if not 'library.html' in template:
        paginator.hide_sort = True

    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except InvalidPage:
        try:
            page = paginator.page(paginator.num_pages)
        except:
            raise Http404("Sorry, no results on any pages.")

    groups = TeacherGroup.objects.all().order_by('title')

    tag_cloud = Tag.objects.exclude(score=0).order_by('-score')[:TAG_CLOUD_MAX]
    tag_cloud_sorted = sorted(tag_cloud, key=lambda o: o.text)

    #top_level_categories = Category.objects.filter(parent__exact=None).order_by('name')

    

    context = {
        'page': page,
        'paginator': paginator,
        'query': query,
        'suggestion': None,
        'tags': tag_cloud_sorted,
        'groups': groups,
        'categories': category_dictionary(),
        'libhidden' : hide_lib_setting.value,
    }

    return render_to_response(template, context, context_instance=RequestContext(request))


def get_results(model=ContentItem, source=None, query=None, category=None, tags=None, exclude_hidden=False, sort_by='date_added'):

    sqs = model.objects.all()

    #sqs = SearchQuerySet().models(model).exclude(categories=-1) # .all() seems to be broken, so here's a failing filter
    total_count = 0
    this_count = 0
    other_count = 0
    if model == ContentItem:
        sqs = sqs.order_by(sort_by)
    else:
        sqs = sqs.order_by('-id')

    if exclude_hidden == True:
        #sqs = sqs.exclude(hidden=True)
        if model==ContentItem:
            hidden_list = ContentItem.objects.filter(hidden=True).values_list(u'pk', flat=True)
            if hidden_list is not None:
                sqs = sqs.exclude(django_id__in=hidden_list)
                
    if query:
        sqs = sqs.filter(text=Clean(query))

    if category and category != "0":
        parent_category = Category.objects.get(pk=category)
        category_id_list = parent_category.all_my_children()
        sqs = sqs.filter(categories__in=category_id_list)

    if tags:
        sq = SQ()
        for tag in tags:
            sq.add(SQ(tags=tag), SQ.AND)
        sqs = sqs.filter(sq)


    total_count = sqs.count()

    if model == ContentItem:
        if source != 'both':
            if source == 'uploaded':
                sqs = sqs.exclude(uploaded=False)
            else:
                sqs = sqs.exclude(uploaded=True)
            other_count = total_count - sqs.count()
            this_count = total_count - other_count

    paginator = Paginator(sqs, RESULTS_PER_PAGE)

    #to display result counts on tabs
    paginator.total_count = total_count
    paginator.this_count = this_count
    paginator.other_count = other_count

    return paginator

def autocomplete(request):
    query = SearchQuerySet().filter(autocomplete=request.GET.get('q', '')).order_by('title')[:5]

    suggested_items = [result.title for result in query]

    json_displayed = json.dumps({
        'results': suggested_items
    })
    return HttpResponse(json_displayed, content_type='application/json')

@login_required
def toggle_view(request):
    #change the value of the session flag to show the desired view
    # NOTE: student view mean the teacher viewing the site as a student
    refferer = request.META.get('HTTP_REFERER')
    if request.session['viewType'] == "teacher":
        request.session['viewType'] = "student"
    else:
        request.session['viewType'] = "teacher"
    return HttpResponseRedirect('/')

@login_required
def toggle_library(request):
    refferer = request.META.get('HTTP_REFERER')
    hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})
    val = hide_lib_setting.value
    if val == "True":
        val = False
    else:
        val = True
    hide_lib_setting.value = val
    hide_lib_setting.save()
    return HttpResponseRedirect(refferer)

@login_required
def toggle_internet(request):
    referer = request.META.get('HTTP_REFERER')

    try:
        hw_api = EasyconnectApApi()
        current_mode = hw_api.get_internet_mode()
    except Exception as e:
        #logger.error('Could not get hardware internet status')
        #logger.exception(e)
        return HttpResponseRedirect(referer)

    if current_mode == 2:
        hw_api.set_internet_mode(0) # turns net off
    else:
        hw_api.set_internet_mode(2) # full net access

    return HttpResponseRedirect(referer)

#a hook to create a session flag specifying the type of view
from django.contrib.auth.models import User
def login_hook(sender, user, request, **kwargs):
    #is_superuser = User.objects.get(pk=userid).is_superuser or False
    if user.is_superuser:
        request.session['viewType'] = "admin"
    else:
        request.session['viewType'] = "teacher"

user_logged_in.connect(login_hook)

class ContentItemList(ListView):
    template_name = 'browse/index.html'
    context_object_name = 'file_list'

    def get_context_data(self, **kwargs):
        context = super(ContentItemList, self).get_context_data(**kwargs)
        teacher = self.request.user.is_authenticated()
        shown_featured_items = ContentItem.objects.filter(featured=True)

        if 'categories' in self.kwargs:
            category_names = self.kwargs['categories'].split('/')
            context['categories'] = category_names

            if len(category_names) > 1:
                parent = category_names[-2]
            else:
                parent = None

            category = get_object_or_404(Category, name=category_names[-1], parent__name=parent)
            shown_featured_items = shown_featured_items.filter(item__categories=category)

        if not teacher:
            shown_featured_items = shown_featured_items.exclude(hidden=True)

        context['featured_list'] = shown_featured_items

        return context

    def get_queryset(self):
        teacher = self.request.user.is_authenticated()
        file_list = ContentItem.objects.exclude(featured=True)
        category = None

        if 'categories' in self.kwargs:
            category_names = self.kwargs['categories'].split('/')

            if len(category_names) > 1:
                parent = category_names[-2]
            else:
                parent = None

            category = get_object_or_404(Category, name=category_names[-1], parent__name=parent)

            file_list = file_list.filter(item__categories=category)

        if not teacher:
            file_list = file_list.exclude(hidden=True)

        return file_list
class ContentItemDetail(DetailView):
    model = ContentItem
    template_name = 'browse/detail.html'
    context_object_name = 'item'
    pk_url_kwarg = 'item_id'

    def get_context_data(self, **kwargs):
        context = super(ContentItemDetail, self).get_context_data(**kwargs)
        context['group_form'] = GroupItems
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return self.model.objects.all()
        else:
            return self.model.objects.filter(hidden=False)

class ContentItemEdit(UpdateView):
    template_name = 'browse/edit.html'
    form_class = UploadForm
    model = ContentItem
    # success_url = '/'
    def get_success_url(self):
        return reverse('detail', kwargs={'item_id':self.kwargs['id']})
    def get_object(self, query_set=None):
        obj = ContentItem.objects.get(id=self.kwargs['id'])
        return obj

# @login_required
class ContentItemDelete(DeleteView):
    template_name = 'browse/delete.html'
    model = ContentItem
    success_url = '/'
    def get_object(self, query_set=None):
        obj = ContentItem.objects.get(id=self.kwargs['id'])
        return obj


class TeacherGroupDetail(ListView):
    template_name = 'browse/lesson_detail.html'
    context_object_name = 'file_list'

    def get_context_data(self, **kwargs):
        context = super(TeacherGroupDetail, self).get_context_data(**kwargs)
        context['group'] = get_object_or_404(TeacherGroup, pk=self.kwargs['lesson_id'])
        return context

    def get_queryset(self):
        lesson_items = ContentItem.objects.all()

        if not self.request.user.is_authenticated():
            lesson_items = lesson_items.exclude(hidden=True)

        return lesson_items.filter(teachergroup__pk=self.kwargs['lesson_id'])

def home(request, template='browse/index.html'):
    """
    home tab showing featured lessons and items
    """
    featured_lessons = TeacherGroup.objects.filter(featured=True).order_by('title')
    featured_items = ContentItem.objects.filter(featured=True).order_by('title')

    if not request.user.is_authenticated():
        featured_items = featured_items.exclude(hidden=True)

    hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})

    context = {
        'featured_items': featured_items[:10],
        'featured_lessons': featured_lessons[:10],
        'libhidden' : hide_lib_setting.value,
    }

    return render_to_response(template, context, context_instance=RequestContext(request))


def lesson_detail(request, template='browse/lesson_detail.html', **kwargs):
    """
    displays the content items within a lesson
    """
    hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})

    lesson = get_object_or_404(TeacherGroup, pk=kwargs['lesson_id'])
    lesson_items = ContentItem.objects.filter(teachergroup__pk=kwargs['lesson_id'])

    if not request.user.is_authenticated():
        lesson_items = lesson_items.exclude(hidden=True)

    paginator = Paginator(lesson_items, RESULTS_PER_PAGE)

    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except InvalidPage:
        try:
            page = paginator.page(paginator.num_pages)
        except:
            raise Http404("Sorry, no results on any pages.")

    context = {
        'lesson': lesson,
        'page': page,
        'paginator': paginator,
        'libhidden' : hide_lib_setting.value,

    }
    return render_to_response(template, context, context_instance=RequestContext(request))

def contentitem_detail(request, template='browse/detail.html'):
    """
    detail on item to be loaded into modal window
    """
    if request.GET and request.is_ajax():
        item = ContentItem.objects.get(pk=request.GET['id'])

    context = {
        'item': item,
    }

    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def upload_file(request):
    tags_list = list(Tag.objects.values_list('text', flat=True))
    tags_json = json.dumps(tags_list)
    if request.method == 'POST':
        try:
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                upload_handler(request)
                for filename, file in request.FILES.iteritems():
                    name = request.FILES[filename].name
                n = Log(text='file '+name+' upladed successfully', datetime= timezone.now(), logType='noti')
                n.save()
                return HttpResponseRedirect(request.POST['next'])

        except:
            n = Log(text='The was an error when Uploading file', datetime= timezone.now(), logType='err')
            n.save()
    else:
        form = UploadForm()
    try:
        return render(request, 'browse/upload.html', {'form': form, 'tags_json': tags_json, 'categories': category_dictionary()})
    except:
        n = Log(text='The was an error when opening the upload page', datetime= timezone.now(), logType='err')
        n.save()

@login_required
def add_new_model(request, model_name):
    if (model_name.lower() == model_name):
        normal_model_name = model_name.capitalize()
    else:
        normal_model_name = model_name
    app_list = get_apps()
    for app in app_list:
        for model in get_models(app):
            if model.__name__ == normal_model_name:
                form = modelform_factory(model)
                if request.method == 'POST':
                    form = form(request.POST)
                    if form.is_valid():
                        try:
                            new_obj = form.save()
                        except forms.ValidationError as error:
                            new_obj = None
                        if new_obj:
                            return HttpResponse('<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script>' % \
                                (escape(new_obj._get_pk_val()), escape(new_obj)))
                else:
                    form = form()
                page_context = {'form': form, 'field': normal_model_name}
                return render_to_response('browse/popup.html', page_context, context_instance=RequestContext(request))

# @receiver(pre_save, sender=ContentItem)
# def pre_check_tag_signal(sender, **kwargs):
#     for tag in kwargs['instance'].tags.all():
#         print tag.text 
#         t = Tag.objects.get_or_create(text=tag.text)


#this looks terribly inneficient
#changed from post_save to post_delete due to timing issues.
'''
@receiver(post_delete, sender=ContentItem)
'''
def check_tag_signal(sender, instance, created, **kwargs):
    # if kwargs['created']:
    if created:
        item_taged = ContentItem.objects.all()
        tag_to_be_deleted = []
        tags_to_keep = []
        for item in item_taged:
            if not item.tags.all():
                pass
            else:
                for tag in item.tags.all():
                    tags_to_keep.append(tag)
            tags_to_keep = list(set(tags_to_keep))
        all_tags = Tag.objects.all()
        for tag in all_tags:
            if tag not in tags_to_keep:
                print(tag.text +" Will be deleted")
                tag.delete()


@login_required
def hide_item(request, id):
    ci = ContentItem.objects.get(pk=id)
    if request.method == 'POST':
        try:
            i = ContentItem.objects.get(pk=id)
            i.hidden = True
            i.save()
            print("item was found")
        except Exception as e:
            i = ContentItem.objects.get(pk=id)
            i.hidden = True
            i.save()
            print("could not find item")
        return HttpResponseRedirect('/')
    else:
        item = ContentItem.objects.get(pk=id).title
        return render(request, 'browse/hide.html', {'item':item, 'item_id': id})

@login_required
def unhide_item(request, id):
    try:
        i = ContentItem.objects.get(pk=id)
        i.hidden = False
        i.save()
    except Exception as e:
        pass
    return HttpResponseRedirect('/')

@login_required
def unfeature_item(request, id):
    try:
        i = TeacContentItem.objects.get(pk=id)
        i.featured = False
        i.save()
    except Exception as e:
        pass
    return HttpResponseRedirect('/')

@login_required
def feature_item(request, id):
    if request.method == 'POST':
        try:
            i = ContentItem.objects.get(pk=id)
            i.featured = True
            i.save()
        except Exception as e:
            i = ContentItem.objects.get(pk=id)
            i.featured = True
            i.save()
        return HttpResponseRedirect('/')
    else:
        item = ContentItem.objects.get(pk=id).title
        return render(request, 'browse/feature.html', {'item':item, 'item_id': id})

@login_required
def add_item_to_group(request, id):
    if request.method == 'POST':
        itemToGroup = ContentItem.objects.get(pk=id)
        groupId = request.POST['title']
        group = TeacherGroup.objects.get(pk=groupId)
        (addMember, created) = TeacherGroupMembership.objects.get_or_create(item = itemToGroup, group = group)
        addMember.save()
    return HttpResponseRedirect('/detail/'+id)

class AjaxableResponseMixin(object):
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return self.render_to_json_response(data)
        else:
            return response

class ContentItemModal(AjaxableResponseMixin, UpdateView):
    template_name = 'browse/edit.html'
    form_class = UploadForm
    model = ContentItem
    # success_url = '/'
    def get_object(self, query_set=None):
        obj = ContentItem.objects.get(id=1)
        return obj

def contentitem_frame(request, template='browse/contentframe.html'):
    """
    content piece to be viewed in page with header and back button
    """
    url = request.GET['item_url']
    return render_to_response(template, {'item_url': url})
