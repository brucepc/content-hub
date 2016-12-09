import logging
import os

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import stringfilter

from contentimport.models import TeacherGroup, Category, Tag

logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag(takes_context=True)
def ec_searchbox(context, **kwargs):
    """
    spit out a search box depending on url
    """
    request = context['request']
    url_name = request.resolver_match.url_name
    existing_query = request.GET.get('q', None)

    # lessons
    if url_name == 'lessons' or url_name == 'group-detail':
        url = reverse('lessons')
        placeholder = 'Search lessons...'
    else:
        # all else
        url = reverse('library')
        placeholder = 'Search library...'

        # If it is the library, we want to redirect to '/preloaded' or '/uploaded' if needed
        if 'source' in request.resolver_match.kwargs.keys():
            url += request.resolver_match.kwargs['source'] + '/'

    html = "<form method='get' action='" + url +"' id='search'>"
    html += "<input id='ac_search' name='q' type='search' autocomplete='off' placeholder='" + placeholder + "'"

    if existing_query:
        html += " value='" + str(existing_query) + "'"

    html += " />"
    html += "<button type='submit'></button>"
    html += "</form>"

    return html

@register.simple_tag(takes_context=True)
def preserve_get(context):
    """
    used to read the current get querys and add them to page links so they don't get lost
    you need to put a ? before the tag and an & after if you're adding extra queries
    """
    try:
        request = context['request']
    except:
        actual_context = context['context'] # passed context from ec_paginator
        request = actual_context['request']

    if request.GET:
        query_dict = request.GET.copy()

        if 'createlesson' in query_dict: del query_dict['createlesson']
        if 'page' in query_dict: del query_dict['page']
        if 'lesson' in query_dict: del query_dict['lesson']
        if 'sort_by' in query_dict: del query_dict['sort_by']
        if 't' in query_dict: del query_dict['t']

        if len(query_dict.items()) > 0:
            query = query_dict.urlencode()
            return query

    return ''

@register.simple_tag(takes_context=True)
def tab_active(context, **kwargs):
    request = context['request']

    if 'source' in kwargs.keys() and 'source' in request.resolver_match.kwargs.keys():
        if kwargs['source'] == request.resolver_match.kwargs['source']:
            return 'activeTab'
    
    elif 'source' in kwargs.keys():
        if kwargs['source'] == 'preloaded': # 'preloaded' is active by default
            return 'activeTab'

    return ''

@register.simple_tag(takes_context=True)
def tabActive(context, **kwargs):
    request = context['request']

    url_name = request.resolver_match.url_name
    tab = kwargs.get('tab', None)

    #logger.info('url_name: ' + str(url_name))
    #logger.info('tab: ' + str(tab))

    aliases = {
        'home': ['index', 'home'],
        'lessons': ['lessons', 'group-detail'],
        'library': ['library', 'upload'],
    }

    alias_list = aliases.get(tab, None)

    if alias_list is not None:
        if url_name in alias_list:
            if kwargs.get('below', False):
                return "<li class='tabActiveBelow'>"
            else:
                return "<li class='tabActive'>"

    return '<li>'


@register.simple_tag(takes_context=True)
def tagActive(context, tag_id):
    """
    return 'on' to be used as class name if tag's id is in the url GET query
    """
    request = context['request']
    tag_list = request.GET.getlist('t', None)

    if tag_list is not None:
        if str(tag_id) in tag_list: return 'on'

    return ''


@register.assignment_tag(takes_context=True)
def is_source(context, **kwargs):

    request = context['request']

    if 'source' in kwargs.keys() and 'source' in request.resolver_match.kwargs.keys():
        if kwargs['source'] == request.resolver_match.kwargs['source']:
            return True

    elif 'source' in kwargs.keys():
        if kwargs['source'] == 'preloaded': # 'preloaded' is the default if there's no source
            return True

    return False

@register.assignment_tag(takes_context=True)
def breadcrumbs(context):

    request = context['request']
    url_name = request.resolver_match.url_name # args, kwargs, url_name

    #logger.info(request.resolver_match)
    #logger.info(request.GET)

    link = {
        'home':    ['Home', 'index'],
        'lessons': ['Lessons', 'lessons'],
        'library': ['Library', 'library'],
        'upload':  ['Upload', 'upload'],
    }

    r_dict = {
        'group-detail': [ link['lessons'] ],
        'home':    [ ],
        'lessons': [ link['lessons'] ],
        'library': [ link['library'] ],
        'upload':  [ link['library'], link['upload'] ],
    }

    response = r_dict.get(url_name, [])

    response.insert(0, link['home']) # everything starts with home

    for item in response:
        item[1] = reverse(item[1])

    # Library is a special case, there might be categories etc
    if url_name == 'library':
        kwargs = request.resolver_match.kwargs

        # We only care about source if user is logged in
        if request.user.is_authenticated():
            source = kwargs.get('source', None)
            if source is None:
                source = 'preloaded' # preloaded is default

            s_url = reverse('library', kwargs={'source': source})
            response.append([ source, s_url ]) # TODO: capitalise first letter...

        if request.GET:
            category_id = request.GET.get('c', None)

            hierarchy = []
            while category_id is not None:
                try:
                    category = Category.objects.get(pk=category_id)
                except:
                    category_id = None
                else:
                    hierarchy.append( [ category.name, reverse('library') + '?c=' + str(category.id) ] )

                    if category.parent:
                        category_id = category.parent.id
                    else:
                        category_id = None

            if hierarchy:
                hierarchy.reverse()

                for cat in hierarchy:
                    response.append( [ cat[0], cat[1] ])

    # Lesson detail page is a special case
    if url_name == 'group-detail':
        kwargs = request.resolver_match.kwargs

        lesson_id = kwargs.get('lesson_id', None)
        if lesson_id is not None:
            group = TeacherGroup.objects.get(pk=lesson_id)
            g_url = reverse('group-detail', kwargs={'lesson_id': lesson_id})
            response.append( [ group.title, g_url ] )

    # Add a crumb for search query if there is one
    if url_name == 'library' or url_name == 'lessons':
        if request.GET:
            search_query = request.GET.get('q', None)
            if search_query is not None:
                response.append( [ 'Search: "' + search_query + '"', '' ])

            # Add a crumb for tags if there are some applied
            tag_query = request.GET.getlist('t', [])
            #logger.info(tag_query)
            number_of_tags = len(tag_query)
            if number_of_tags > 0:
                #logger.info(number_of_tags)
                try:
                    tag_names = Tag.objects.values('text').filter(pk__in=tag_query)
                except:
                    pass
                else:
                    crumb_string = ""
                    crumb_string_end = ""
                    if number_of_tags > 2:
                        crumb_string_end = " and " + str(number_of_tags - 2) + " more"
                        tag_names = tag_names[:2]

                    
                    for tag in tag_names:
                        crumb_string = crumb_string + '"' + tag.get('text', '') + '"'
                        if number_of_tags > 1:
                            crumb_string = crumb_string + ", "

                        crumb_string = crumb_string + " "

                    crumb_string = "Tags: " + crumb_string + crumb_string_end

                    #logger.info(crumb_string)

                    response.append( [ crumb_string, '' ] )


    for item in response:
        item[0] = item[0].capitalize()

    return response


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# (see "mediaIcon" in style.css)
CSS_ICON_TYPES = [
    'ai',
    'apk',
    'avi',
    'bmp',
    'css',
    'dir',
    'dll',
    'dmg',
    'doc',
    'docx',
    'eps',
    'exe',
    'fla',
    'gif',
    'gz',
    'gzip',
    'html',
    'indd',
    'iso',
    'jpeg',
    'jpg',
    'js',
    'midi',
    'mov',
    'mp3',
    'mp4',
    'mpeg',
    'otf',
    'pdf',
    'php',
    'png',
    'ppt',
    'pptx',
    'psd',
    'pub',
    'rar',
    'rtf',
    'svg',
    'swf',
    'tar',
    'tiff',
    'txt',
    'url',
    'wav',
    'wma',
    'xls',
    'xlsx',
    'xml',
    'zip',
]

# anchor file names with dots in weird places are tricky...
we_dont_care, ANCHOR_FILE_NAME_EXTENSION = os.path.splitext(getattr(settings, 'ANCHOR_FILE_NAME', '_ec.anchor'))

# A list of exceptions to the file extension == css class rule
FILE_TYPE_TRANSLATIONS = {
    ANCHOR_FILE_NAME_EXTENSION[1:]: 'dir',
}

@register.filter
@stringfilter
def get_extension(value):
    """
    takes in a file path and returns a css class based on the extension
    """
    still_dont_care, file_extension = os.path.splitext(value)
    no_dot = file_extension[1:]

    if no_dot in CSS_ICON_TYPES:
        # This extension is on the list of css classes, so just pass it straight through
        css_class = no_dot
    else:
        # Check if this extension needs to be translated, if not just use 'generic'
        css_class = FILE_TYPE_TRANSLATIONS.get(no_dot, 'generic')

    return css_class