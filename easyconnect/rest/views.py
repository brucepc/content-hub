from contentimport.models import ContentItem, TeacherGroup, Category, Tag, TeacherGroup, TeacherGroupMembership, SiteSetting, Package, PackageMembership, Tile
from rest_framework import viewsets, filters, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action, link
from serializers import ContentItemSerializer, ContentItemSerializerPost, ContentItemSerializerPut, ContentItemSerializerGet, CategorySerializer, CategoryTreeSerializer, TagSerializer, TeacherGroupSerializer, TeacherGroupSerializerNested, UserSerializer, PackageSerializer, TileSerializer, TileSerializerPut, TileSerializerTranslate_GetOnly
from django.db.models import Count, Max
from django.contrib.auth import login, logout
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.parsers import MultiPartParser
from rest_framework.settings import api_settings
from contentimport.lib import upload_handler, icon_upload_handler
import re #not a typo
from rest_framework.exceptions import ParseError
import json
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from easyconnect.context_processors import battery_status
from easyconnect.hw_api import EasyconnectApApi
from rest.pagination import CustomPaginationSerializer

from rest_framework.authtoken import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

#from contentimport.lib import contentitem_pre_cleanup 

from browse.views import check_tag_signal #cleanup empty tags post edit
from contentimport.importer import Importer #brilliant!
import distutils
from easyconnect import settings
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, authentication_classes
from contentimport.lib import isThereEnoughSpace
from contentimport.lib import getSaveLocation
from contentimport.lib import getMediaURL
from contentimport.lib import get_file_size

MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', None)
MEDIA_URL = getattr(settings, 'MEDIA_URL', None)
HDD_DIR = getattr(settings, 'HDD_DIR', None)
PATCH_UPLOAD_DIR = getattr(settings, 'PATCH_UPLOAD_DIR', None)
PATCH_UPPER_EXTRACT_DIR = getattr(settings, 'PATCH_UPPER_EXTRACT_DIR', None)
PATCH_EXTRACT_DIR = getattr(settings, 'PATCH_EXTRACT_DIR', None)
PATCH_APPLY_DIR = getattr(settings, 'PATCH_APPLY_DIR', None)
from rest_framework.exceptions import ParseError
from rest.serializers import ContentItemSerializer_IE9_Error


class ContentItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ContentItems to be viewed or edited.
    """
    queryset = ContentItem.objects.all()
    serializer_class = ContentItemSerializer
    ordering = ('title',)

    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('featured', 'uploaded', 'hidden',)
    ordering_fields = ('title', 'date_added')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            if not self.pre_save(serializer.object):
                return Response({}, status=status.HTTP_201_CREATED)# For IMS
            if not serializer.object.uploaded and serializer.object.out_of_space:
                return Response({}, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}

    def pre_save(self, obj):
        if self.request.method == 'POST':
            new_file = self.request.FILES['content_file']
            obj.mime_type = new_file.content_type
            obj.file_size = new_file.size
            obj.content_file = upload_handler(self.request)
            if obj.content_file == None:
                obj.uploaded = False
                obj.out_of_space = True
                return True
            #if the object is an IMS package or zip
            elif str(obj.content_file).lower().endswith('.zip'):
                metadata={}
                metadata['title'] = obj.title
                metadata['description'] = obj.description

                #metadata['tags']=obj._m2m_data['tags']
                metadata['tags'] = { 'ids': [] } 
                for tag in obj._m2m_data['tags']:
                    metadata['tags']['ids'].append(tag.id)
                #metadata['categories']=obj._m2m_data['categories']
                metadata['categories']= { 'ids': [] }
                for cat in obj._m2m_data['categories']:
                    metadata['categories']['ids'].append(cat.id)

                path = str(obj.content_file).replace(MEDIA_URL, MEDIA_ROOT)
                Importer(path, metadata=metadata, zip_unpack=False)
                return False
            obj.uploaded = True
            return True

    def post_save(self, obj, created):
        if self.request.method == 'PUT':
            empty_tags = Tag.objects.annotate(ci_count=Count('contentitem')).filter(ci_count=0)
            if empty_tags:
                empty_tags.delete()
            #check_tag_signal(self, obj, created=True)   #do tag cleanup

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method == 'POST':
            serializer_class = ContentItemSerializerPost
        if self.request.method == 'PUT':
            serializer_class = ContentItemSerializerPut
        if self.request.method == 'GET':
            serializer_class = ContentItemSerializerGet
        return serializer_class

    def get_queryset(self):
        queryset = ContentItem.objects.all()
        is_search = self.request.QUERY_PARAMS.get('search', None)
        query_cat = self.request.QUERY_PARAMS.get('c', None)
        query_tag = self.request.QUERY_PARAMS.get('t', None)
        return ApplyFilterSet(queryset, is_search, query_cat, query_tag)

# Specific class to deal with file upload for IE9-ONLY
class IE9_ContentItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ContentItems to be posted from IE9.
    """
    permission_classes = (AllowAny, )

    queryset = ContentItem.objects.all()
    serializer_class = ContentItemSerializer
    IE9_Auth_Error = False

    def create(self, request, *args, **kwargs):
        token_valid = False
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if request.DATA and request.DATA['authenticity_token']:
            try:
                tok = Token.objects.get(key=request.DATA['authenticity_token'])
                if tok:
                    token_valid = True
            except:
                self.IE9_Auth_Error = True

        if token_valid:
            if serializer.is_valid():
                if not self.pre_save(serializer.object):
                    return Response({}, status=status.HTTP_201_CREATED)# For IMS
                self.object = serializer.save(force_insert=True)
                self.post_save(self.object, created=True)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED,
                                headers=headers)
        else:
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}

    def pre_save(self, obj):
        if self.request.method == 'POST':
            new_file = self.request.FILES['content_file']
            obj.mime_type = new_file.content_type
            obj.file_size = new_file.size
            obj.content_file = upload_handler(self.request)
            #if the object is an IMS package or zip
            if str(obj.content_file).lower().endswith('.zip'):
                metadata={}
                metadata['title'] = obj.title
                metadata['description'] = obj.description
                metadata['tags']=obj._m2m_data['tags']
                metadata['categories']=obj._m2m_data['categories']
                path = str(obj.content_file).replace(MEDIA_URL, MEDIA_ROOT)
                Importer(path, metadata=metadata, zip_unpack=False)
                return False
            obj.uploaded = True
            return True

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method == 'POST':
            serializer_class = ContentItemSerializerPost
        if self.IE9_Auth_Error:
            serializer_class = ContentItemSerializer_IE9_Error
        return serializer_class


#method to apply filters, common to both get-contentitems & get-tagcloud
def ApplyFilterSet(queryset, is_search, query_cat, query_tag):
    if is_search:
        query = is_search
        tagIds = Tag.objects.filter(text__icontains=query).values_list('pk', flat=True)
        C_resultInTitle = ContentItem.objects.filter(title__icontains=query)
        C_resultInTags = ContentItem.objects.filter(tags__pk__in=tagIds)
        C_resultInDescription = ContentItem.objects.filter(description__icontains=query)
        queryset = ContentItem.objects.none()
        queryset = C_resultInTitle | C_resultInTags | C_resultInDescription 
        queryset = queryset.distinct() #fix to possible bug, was causing duplication in union operation
    if query_cat is not None:
        if query_cat == '-1':
            queryset = queryset.filter(categories=None)
        else:
            try:
                root_cat = Category.objects.get(pk=query_cat)
                cat_tree = root_cat.all_my_children()
                queryset = queryset.filter(categories__id__in=cat_tree)
            except Category.DoesNotExist:
                queryset = ContentItem.objects.none()   #cat doesnt exist return empty queryset
                pass
    if query_tag is not None:
        queryset = queryset.filter(tags__id=query_tag)
    return queryset

import os
from easyconnect.settings import MEDIA_ROOT, MEDIA_URL
class ContentItemBulkDelete(APIView):
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data.get('ids'):
            idlist = in_data['ids']

            for id in idlist:
                try:
                    exists = ContentItem.objects.get(pk=id)
                    if exists.uploaded:
                        path = str(exists.content_file).replace(MEDIA_URL, MEDIA_ROOT)
                        exists.delete()
                        # Delete the file on disk
                        # Do not delete if html file as this could be a common file from an IMS package
                        if not (path.lower().endswith('html') or path.lower().endswith('htm')):
                            #instance.content_file.delete(save=False)
                            try:
                                os.remove(path)
                            except:
                                pass
                except ContentItem.DoesNotExist:
                    pass
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Categories to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ('name',)
    paginate_by = None
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            #strip leading and trailing whitespace and check for non-empty
            new_text = serializer.object.name.strip()
            if new_text:
                serializer.object.name = new_text
            else:
                return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)

            #get siblings including none case for root
            siblings = {}
            if serializer.object.parent:
                siblings = Category.objects.filter(parent__pk=serializer.object.parent.id)
            else:
                siblings = Category.objects.filter(parent=None)

            #compare each sibling to new name
            for sibling in siblings:
                if sibling.name.lower() == new_text.lower():
                    return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryTree(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(parent=None)
    paginate_by = 5000
    serializer_class = CategoryTreeSerializer

   
class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Tags to be viewed or edited.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    ordering = None
    paginate_by = 20

    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('text',)

    @link()
    def contentitems(self, request, pk=None):
        """
        Method on tags that returns a list of associated content items.
        """
        serializer = ContentItemSerializer(ContentItem.objects.filter(tags__id=pk), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            new_text = serializer.object.text.strip()
            #new_text = self.sanitize(new_text)
            if new_text:
                serializer.object.text = new_text
            else:
                return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)

            existing = Tag.objects.filter(text=new_text)
            if existing:
                return Response(TagSerializer(existing[0]).data, status=status.HTTP_200_OK)
            else:
                self.pre_save(serializer.object)
                self.object = serializer.save(force_insert=True)
                self.post_save(self.object, created=True)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED,
                                headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}

    def sanitize(e, tag):
        tag = re.sub(r"[^\w\s]", '', tag)
        return re.sub(r"\s+", '-', tag)
    
    
    def get_queryset(self):
        locked = self.request.QUERY_PARAMS.get('locked', None)
        if locked:
            if locked == 'true':
                queryset = Tag.objects.filter(locked=True)
            else:
                queryset = Tag.objects.filter(locked=False)
        else:
            queryset = Tag.objects.all()
        return queryset
    
    

    empty_error = "Empty list and '%(class_name)s.allow_empty' is False."
    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())
        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        if not self.allow_empty and not self.object_list:
            warnings.warn(
                'The `allow_empty` parameter is due to be deprecated. '
                'To use `allow_empty=False` style behavior, You should override '
                '`get_queryset()` and explicitly raise a 404 on empty querysets.',
                PendingDeprecationWarning
            )
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

        
        #apply filters to set for new cloud & filtering implementation
        itemset = ContentItem.objects.all()
        is_search = self.request.QUERY_PARAMS.get('search', None)
        query_cat = self.request.QUERY_PARAMS.get('c', None)
        
        itemset = ApplyFilterSet(itemset, is_search, query_cat, None)
        
        tags = itemset.values('tags').annotate(n=Count("pk")).values_list('tags')
        self.object_list = self.object_list.filter(pk__in=tags)

        #manual override for the ordering, to allow sorting on calculated field 'uses'
        #ordering permitted by text, score and uses
        ordering = self.request.QUERY_PARAMS.get('ordering', None)
        allowed_ordering = [
            'text',
            '-text',
            'score',
            '-score',
        ]
        derrived_ordering = [
            'uses',
            '-uses',
        ]
        if ordering:
            if ordering in allowed_ordering:
                self.object_list = self.object_list.order_by(ordering)
            elif ordering in derrived_ordering:
                ord = '-c_count' if ordering.startswith('-') else 'c_count'
                self.object_list = self.object_list.annotate(c_count=Count('contentitem')).order_by(ord)
        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)


class TeacherGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Lessons to be viewed or edited.
    """
    queryset = TeacherGroup.objects.all()
    serializer_class = TeacherGroupSerializer
    ordering = ('title',)
    
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('featured',)
    ordering_fields = ('title', 'updated')

    def retrieve(self, request, pk=None):
        queryset = TeacherGroup.objects.all()
        teacherGroup = get_object_or_404(queryset, pk=pk)
        serializer = TeacherGroupSerializerNested(teacherGroup)
        return Response(serializer.data)
    
    
    def get_queryset(self):
        queryset = TeacherGroup.objects.all()
        is_search = self.request.QUERY_PARAMS.get('search', None)
        if is_search:
            query = is_search
            L_resultInTitle = TeacherGroup.objects.filter(title__icontains=query)
            return L_resultInTitle
        else:
            return queryset

class AuthView(APIView):
    Authentication_classes = (TokenAuthentication,)

    def get(self, request, format=None):
        request.user.backend = 'django.contrib.auth.backends.ModelBackend' #auth is already done by DRF, but not recognised by login method, this is a workaround.
        login(request, request.user)
        return Response(UserSerializer(request.user).data)

class SearchView_Lessons(APIView):
    permission_classes = (AllowAny, )

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data['data']:
            query = str(in_data['data'])
            L_resultInTitle = TeacherGroup.objects.filter(title__icontains=query)
            L_combined = L_resultInTitle
            return Response(TeacherGroupSerializer(L_combined).data)


class SearchView_ContentItems(APIView):
    permission_classes = (AllowAny, )

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data.get('data'):
            query = str(in_data['data'])

            tagIds = Tag.objects.filter(text__icontains=query).values_list('pk', flat=True)
            C_resultInTitle = ContentItem.objects.filter(title__icontains=query)
            C_resultInTags = ContentItem.objects.filter(tags__pk__in=tagIds)
            C_resultInDescription = ContentItem.objects.filter(description__icontains=query)

            C_combined = C_resultInTitle | C_resultInTags | C_resultInDescription

            C_filtered = None
            if in_data.get('uploaded'):
                searchfilter = in_data['uploaded'] == 'True'
                C_filtered = C_combined.filter(uploaded=searchfilter)
                C_combined = C_filtered

            return Response(ContentItemSerializer(C_combined).data)


class Settings_Library(APIView):

    def get(self, request, format=None):
        response = {}
        hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})
        
        #value is a string, so map to boolean
        val = False
        if hide_lib_setting.value == "True":
            val = True
        
        response['library_hidden'] = val
        return Response(response)

    def post(self, request, *args, **kwargs):
        hide_lib_setting, created = SiteSetting.objects.get_or_create(name="hide_library", defaults={'value':False})
        val = hide_lib_setting.value
        if val == "True":
            val = False
        else:
            val = True
        hide_lib_setting.value = val
        hide_lib_setting.save()
        response = {}
        response['library_hidden'] = val
        return Response(response)

class Settings_update_session_viewtype(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        if not request.is_ajax() or not request.method=='POST':
            return HttpResponseNotAllowed(['POST'])
        type = request.QUERY_PARAMS['type'] or ''
        if (type == 'admin'):
            request.session['viewType'] = 'admin'
        elif (type == 'teacher'):
            request.session['viewType'] = 'teacher'
        return HttpResponse('ok')

class Settings_Internet(APIView):

    def get(self, request, format=None):
        response = {}
        status = battery_status(request)
        response['battery'] = status['battery']
        response['internet'] = status['internet']
        return Response(response)

    def post(self, request, *args, **kwargs):
        
        current_mode = 0
        response = {}

        try:
            hw_api = EasyconnectApApi()
            current_mode = hw_api.get_internet_mode()
        except Exception as e:
            pass

        if current_mode == 2:
            hw_api.set_internet_mode(0) # turns net off
            response['internet'] = 0
        else:
            hw_api.set_internet_mode(2) # full net access
            response['internet'] = 2

        return Response(response)


class Settings_SSID(APIView):
    '''
    Expose get/set SSID functionality
    '''
    def get(self, request, format=None):
        response = {}
        hw_api = EasyconnectApApi()
        ssid = hw_api.get_ssid();
        response['ssid'] = ssid

        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        response = {}
        ssid = request.QUERY_PARAMS['ssid']
        hw_api = EasyconnectApApi()
        response['success'] = 'False'
        resp_status = status.HTTP_400_BAD_REQUEST

        if hw_api.set_ssid(ssid):
            response['success'] = 'True'
            resp_status = status.HTTP_200_OK

        return Response(response, status=resp_status)

class Settings_ResetTeacher(APIView):
    '''
    Set teacher account to factory default.
    '''
    def post(self, request, *args, **kwargs):
        response = {}
        hw_api = EasyconnectApApi()
        response['success'] = 'False'
        resp_status = status.HTTP_400_BAD_REQUEST

        if hw_api.reset_teacher_account():
            response['success'] = 'True'
            try:
                #delete all non superuser accounts (should only be one in theory)
                non_superusers = User.objects.filter(is_superuser=False)
                for non_su in non_superusers:
                    non_su.delete()
                #recreate the default
                teach_user = User.objects.create_user(username='teacher', password='teacher')
                teach_user.save()
                Token.objects.create(user=teach_user)
            except e:
                teach_user = User.objects.create_user(username='teacher', password='teacher')
                teach_user.save()
                Token.objects.create(user=teach_user)
                pass
            resp_status = status.HTTP_200_OK
        return Response(response, status=resp_status)

class Settings_CHANGEPASSWORD(APIView):
    '''
    Expose change teacher password functionality
    '''
    def post(self, request, *args, **kwargs):
        response = {}
        response['success'] = 'False'
        in_data = json.loads(request.body)
        oldPassword = in_data['oldPassword']
        newPassword = in_data['newPassword']
        confirmPassword = in_data['confirmPassword']

        if newPassword != confirmPassword:
            response['message'] = _('Passwords do not match.')
            return Response(response, status=status.HTTP_406_NOT_ACCEPTABLE)

        hw_api = EasyconnectApApi()

               
        ext_username, ext_password = hw_api.get_teacher_account()           
        #account = hw_api.get_teacher_account()
        if ext_password != oldPassword:
            response['message'] = _('Invalid password.')
            return Response(response, status=status.HTTP_406_NOT_ACCEPTABLE)

        if hw_api.set_teacher_account(username=ext_username, password=newPassword):
            response['success'] = 'True'


        #if success update in django database
        if response['success'] == 'True':
            try:
                teach_user = User.objects.get(username__exact=ext_username)
                teach_user.set_password(newPassword)
                teach_user.save()
                #Token.objects.create(user=teach_user)
            except e:
                teach_user = User.objects.create_user(username=ext_username, password=newPassword)
                teach_user.save()
                Token.objects.create(user=teach_user)
                pass

        return Response(response)

class Settings_DeviceVersion(APIView):
    '''
    Get the version of CAP device
    '''
    def get(self, request, format=None):
        response = {}
        try:
            hw_api = EasyconnectApApi()
            version = hw_api.get_cap_version()
            response["version"] = version
        except Exception as ex:
            pass
        return Response(response)


class Settings_RemoteManagement(APIView):
    '''
    GET/SET for remote management access
    '''
    def get(self, request, format=None):
        response = {}
        hw_api = EasyconnectApApi()
        response["remotemanagement"] = hw_api.get_remote_management_status() 
        return Response(response)
    
    def post(self, request, *args, **kwargs):
        response = {}
        try:
            toggleTo = request.QUERY_PARAMS['remotemanagement']
        except Exception as ex:
            pass

        hw_api = EasyconnectApApi()
    
        if toggleTo == 'on':
            res = hw_api.start_remote_management() # turns remote management on
            if res:
                response['remotemanagement'] = 1
            else:
                response['remotemanagement'] = -1
                return Response(response, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif toggleTo == 'off':
            hw_api.stop_remote_management() # remote management off
            response['remotemanagement'] = 0


        return Response(response)
        
 # Aidan Commented out code below as per request from Bun 01-06-16
#class Settings_Study(APIView):
#    '''
#    GET/SET for Study
#    '''
#    def get(self, request, format=None):
#        response = {}
#        hw_api = EasyconnectApApi()
#        response["study"] = hw_api.get_study_status() 
#        return Response(response)
  
#    def post(self, request, *args, **kwargs):
#        #tile_title = "Intel® Education Study: Local Administer"
#        current_status = 0
#        response = {}

#        try:
#            hw_api = EasyconnectApApi()
#            current_status = hw_api.get_study_status()
#        except Exception as e:
#            pass
        
#        #try:
#        #    tile = Tile.objects.get(title=tile_title)
#        #except:
#        #    #Hack to test tile creation
#        #    #current_status = 2
#        #    tile = None
        
#        if current_status == 1:
#            res = hw_api.toggle_study(False) # turns study off
#            if res == 0:
#                #if tile:
#                #    tile.delete()
#                response['study'] = 2
#        else:
#            res = hw_api.toggle_study(True) # study on
#            if res == 0: #or res is None: #Hack to test tile creation
#                #if tile is None:
#                #    tile = Tile(title=tile_title, icon="intel_education_study.svg", url_string="http://my.content:9000", teacher_tile = True, hidden = True, read_only = True)
#                #    last_item = Tile.objects.all().aggregate(Max('display_order'))
#                #    tile.display_order = last_item['display_order__max'] + 1    
#                #    tile.save()
#                response['study'] = 1
#            else:
#                response['study'] = hw_api.get_study_status()        

#        return Response(response)
        
from contentimport.views import usb_file_select, usb_import, usb_response
class USB_Util_Upload(APIView):

    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        selected_list = in_data['selected']
        isAsync = True if 'async' in in_data else False
        metadata = {}
        metadata['tags'] = {'ids': in_data['tags']}
        metadata['categories'] = {'ids': in_data['categories']}
        if 'description' in in_data:
            metadata['description'] = in_data['description']
        if 'title' in in_data:
            metadata['title'] = in_data['title']
        microsite = True if 'microsite' in in_data else False

        resp = {}
        if selected_list:
            resp = usb_import(selected_list, metadata, async=isAsync, microsite=microsite)
        return Response(resp)


class USB_Util_Dir(APIView):
    '''
    Enumerate a directory given an ID
    '''
    permission_classes = (AllowAny, ) #DEBUG ONLY: TO BE REMOVED
    def post(self, request, *args, **kwargs):
        req = json.loads(request.body)
        resp = {}
        if req:
            path = req['id']
            if 'filetypes' in req:
                filetypes = req['filetypes'].split(',')
            else:
                filetypes = None
            resp = usb_response(path, filetypes)
        return Response(resp)


'''
Package handling functionality
'''
from easyconnect.settings import MEDIA_ROOT, PRELOAD_CONTENT_DIR, ICONS_DIR, MICROSITE_DIR
from itertools import chain
from rest.UploadProgressCachedHandler import UploadProgressCachedHandler
 
class BasicAuthenticationNoChallenge(BasicAuthentication):
    def authenticate_header(self, request):
        return 'xBasic realm="%s"' % self.www_authenticate_realm


def delete_package_by_path(extractdir):
    idlist = Package.objects.filter(package_file=extractdir).values_list('id', flat=True)
    delete_list_by_id(idlist)
    return True


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    paginate_by = None

    serializer_class = PackageSerializer
    authentication_classes = (BasicAuthenticationNoChallenge, TokenAuthentication,)

    '''
    Rest Get
    '''
    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())
        #get only one occurrence for each zip package filename
        packagelist = Package.objects.filter(preloaded=True).values('package_file').distinct()
        queryset = Package.objects.none()
        for package in packagelist:
            queryset = chain(queryset, self.object_list.filter(package_file=package['package_file'])[:1])
        
        self.object_list = queryset
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)
    
    '''
    Rest Post
    '''
    def create(self, request, *args, **kwargs):
        #try:
            # SHOULD CHECK FOR ZIP INITALLY ALSO
            # write the file to disk
            try:
                if not 'content_file' in request.FILES:
                    return Response({ 'file_error': 'true' }, status=status.HTTP_200_OK)
                
                new_file = request.FILES['content_file']
                #save_dir = MEDIA_ROOT + PRELOAD_CONTENT_DIR #not putting in preloaded root any more
                save_dir = getSaveLocation(new_file.size * 3, MEDIA_ROOT + PRELOAD_CONTENT_DIR)

                #Check if there is 3 times the size of the file available for upload and extraction
                if isThereEnoughSpace(new_file.size * 3, save_dir):
                    fs = FileSystemStorage(location=save_dir)
                    if fs.exists(new_file.name):
                        if (not 'overwrite' in request.DATA) or (not request.DATA['overwrite']):
                            return Response({
                                'status': 'error',
                                'message': 'Package exists, use "overwrite:true" to overwrite'
                                }, status=status.HTTP_200_OK)
                        else:
                            try:
                                #delete_package_by_path(MEDIA_ROOT + PRELOAD_CONTENT_DIR + os.path.splitext(new_file.name)[0])
                                delete_package_by_path(os.path.join(save_dir, os.path.splitext(new_file.name)[0]))
                            except Exception as e:
                                pass
                        #new_file.name = fs.get_available_name(new_file.name)
                    content_file = fs.save(new_file.name, new_file)
                else:
                    return Response({}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                    
                '''
                #file is now in preload source
                #leave it there so it will be picked up on factory reset
                #now copy to the extracted dir & process from there
                try:
                    distutils.file_util.copy_file(save_dir + content_file, MEDIA_ROOT + PRELOAD_CONTENT_DIR + content_file)
                except OSError:
                    pass
                '''

                importJobID = None
                if content_file:
                    #imp = Importer(MEDIA_ROOT + PRELOAD_CONTENT_DIR + content_file, is_preloaded=True, asynchronous=True)
                    imp = Importer(os.path.join(save_dir, content_file), is_preloaded=True, asynchronous=True)
                    importJobID = imp.asyncProcessID
                return Response({ 'importJobID': importJobID, 'status': 'success' }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
       
    '''
    Rest Delete
    '''
    def destroy(self, request, *args, **kwargs):
        exists = self.get_object()
        zippath = ''
        error = { 'status': 'error' }
        try:
            AssocItems = []
            if exists:
                extract_path = exists.package_file
                zippath = MEDIA_ROOT + PRELOAD_CONTENT_DIR + exists.title
                zippathHDD = os.path.join(MEDIA_ROOT, HDD_DIR, PRELOAD_CONTENT_DIR, exists.title)
                associated_ids = Package.objects.filter(package_file=extract_path).values_list('id', flat=True)
                AssocItems = ContentItem.objects.filter(packagemembership__package_id__in=associated_ids)

                pre_delete.disconnect(contentitem_pre_cleanup, sender=ContentItem)
                
                #AssocItems.delete()
                while AssocItems.count():
                    ids = AssocItems.values_list('pk', flat=True)[:100]
                    AssocItems.filter(pk__in = ids).delete()
                pre_delete.connect(contentitem_pre_cleanup, sender=ContentItem)
                    
                empty_tags = Tag.objects.annotate(ci_count=Count('contentitem')).filter(ci_count=0)
                if empty_tags:
                    empty_tags.delete()


                duplicates = Package.objects.filter(package_file=extract_path)
                if duplicates:
                    for d in duplicates:
                        d.delete()
            else:
                error['message'] = 'Package does not exist'
                return Response(error, status=status.HTTP_200_OK)
        except Exception as e:
            error['message'] = 'An error has occured while attempting to delete the package'
            #return Response(error, status=status.HTTP_204_NO_CONTENT)
            return Response(error, status=status.HTTP_200_OK)
        if zippath:
            try:
                if os.path.exists(zippath):
                    os.remove(zippath)
                elif os.path.exists(zippathHDD):
                    os.remove(zippathHDD)
            except:
                pass

            original_zip = zippath.replace('content_dir/', '')
            original_zip_hdd = zippathHDD.replace('content_dir/', '')
            try:
                if os.path.exists(original_zip):
                    os.remove(original_zip)
                elif os.path.exists(original_zip_hdd):
                    os.remove(original_zip_hdd)
            except:
                pass
        return Response({'status':'success'}, status=status.HTTP_200_OK)


class MPT_Package_Path(APIView):
    '''
    MPT accept a path on device and attempt to import it.
    '''
    authentication_classes = (BasicAuthenticationNoChallenge,)

    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if 'path' in in_data:
            mpt_path = in_data['path']
            mpt_root, mpt_filename = os.path.split(mpt_path)

            save_dir = MEDIA_ROOT + PRELOAD_CONTENT_DIR
            save_dir_hdd = os.path.join(MEDIA_ROOT, HDD_DIR, PRELOAD_CONTENT_DIR)
            fs = FileSystemStorage(location=save_dir)
            fsHDD = FileSystemStorage(location=save_dir_hdd)

            if fs.exists(mpt_filename) or fsHDD.exists(mpt_filename):
                if (not 'overwrite' in in_data) or (not in_data['overwrite']):
                    return Response({
                            'status': 'error',
                            'message': 'Package exists, use "overwrite:true" to overwrite'
                            }, status=status.HTTP_200_OK)
                else:
                    try:
                        if fs.exists(mpt_filename):
                            delete_package_by_path(MEDIA_ROOT + PRELOAD_CONTENT_DIR + os.path.splitext(mpt_filename)[0])
                        else:
                            delete_package_by_path(os.path.join(save_dir_hdd, os.path.splitext(mpt_filename)[0]))
                            
                    except Exception as e:
                        pass
            
            try:
                imp = Importer(mpt_path, copy_to_preload=True, metadata={}, asynchronous=True, is_preloaded=True, isMPT=True)
                if imp.MPT_fail:
                    return Response({'status' : 'error', 'message': 'problem with file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                if imp.outOfSpaceError:
                    return Response({'status' : 'error', 'message': 'out of space'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                return Response({ 'status' : 'success' }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({ 'status': 'error', 'message': 'problem with file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({'status': 'error', 'message': 'No path specified'}, status=status.HTTP_200_OK)


from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
'''
Get celery job status from worker threads and return to client, should be polled on a short loop.
'''
@csrf_exempt
def package_processing_progress(request):
    data = 'Fail'
    if request.is_ajax():
        if 'task_id' in request.POST.keys() and request.POST['task_id']:
            task_id = request.POST['task_id']
            task = AsyncResult(task_id)
            if task.state == 'FAILURE' or (task.state == 'SUCCESS' and task.get() == 'FAILURE'):
                data = { 'meta': 'empty_package', 'state' : 'FAILURE' }
            else:
                data = { 'meta': task.result , 'state' : task.state }
        else:
            data = 'No task_id in the request'
    else:
        data = 'This is not an ajax request'
    
    try:
        json_data = json.dumps(data)
    except Exception as e:
        json_data = ''

    return HttpResponse(json_data, mimetype='application/json')


'''
Take a list of package IDs for deletion

'''    

from django.db.models.signals import pre_delete
from contentimport.lib import contentitem_pre_cleanup
def delete_list_by_id(idlist):
    for id in idlist:
        zippath = ''
        extract_path = ''
        try:
            AssocItems = []
            exists = Package.objects.get(pk=id)
                    
            if exists:
                extract_path = exists.package_file
                zippath = save_dir = os.path.join(MEDIA_ROOT + PRELOAD_CONTENT_DIR, exists.title)
                zippathHDD = save_dir = os.path.join(MEDIA_ROOT, HDD_DIR, PRELOAD_CONTENT_DIR, exists.title)
                associated_ids = Package.objects.filter(package_file=extract_path).values_list('id', flat=True)
                AssocItems = ContentItem.objects.filter(packagemembership__package_id__in=associated_ids)


                pre_delete.disconnect(contentitem_pre_cleanup, sender=ContentItem)
                #AssocItems.delete()

                while AssocItems.count():
                    ids = AssocItems.values_list('pk', flat=True)[:100]
                    AssocItems.filter(pk__in = ids).delete()

                pre_delete.connect(contentitem_pre_cleanup, sender=ContentItem)
                    
            #create function for re-use
            empty_tags = Tag.objects.annotate(ci_count=Count('contentitem')).filter(ci_count=0)
            if empty_tags:
                empty_tags.delete()


            exists = Package.objects.filter(package_file=extract_path)
            if exists:
                for ex in exists:
                    ex.delete()

        except Package.DoesNotExist:
            pass

        if zippath:
            try:
                os.remove(zippath)
            except:
                pass

            original_zip = zippath.replace('content_dir/', '')
            try:
                os.remove(original_zip)
            except:
                pass
    
        if zippathHDD:
            try:
                os.remove(zippathHDD)
            except:
                pass

            original_zip = zippathHDD.replace('content_dir/', '')
            try:
                os.remove(original_zip)
            except:
                pass


class PackageBulkDelete(APIView):
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data.get('ids'):
            idlist = in_data['ids']
            delete_list_by_id(idlist)
        return Response(status=status.HTTP_200_OK)
        #else:
        #   return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view([ 'DELETE', ])
@authentication_classes([BasicAuthenticationNoChallenge, TokenAuthentication,])
def deleteteachercontent(request):
    if request:
                
        try:
            AssocItems = []
            teacherPackages = Package.objects.filter(preloaded=False)
            zippath = ''
            for teacherPackage in teacherPackages:
                zippath = teacherPackage.package_file or ''
                AssocItems = ContentItem.objects.filter(packagemembership__package_id=teacherPackage.id)

                for contentItem in AssocItems:
                    contentItem.delete()

                teacherPackage.delete()

                if zippath:
                    try:
                        os.remove(zippath)
                    except:
                        pass

                    original_zip = zippath.replace('content_dir/', '')
                    try:
                        os.remove(original_zip)
                    except:
                        pass

            try:
                teacheritems = ContentItem.objects.filter(uploaded=True)
                for teacheritem in teacheritems:
                    try:
                        path = str(teacheritem.content_file).replace(MEDIA_URL, MEDIA_ROOT)
                        teacheritem.delete()
                        #we dont need to protect html from packages as this is a delete all
                        #if not (path.lower().endswith('html') or path.lower().endswith('htm')):
                        try:
                            os.remove(path)
                        except:
                            pass
                    except ContentItem.DoesNotExist:
                        pass
            except:
                pass

            try:
                lessons = TeacherGroup.objects.all()
                for lesson in lessons:
                    #zippath = teacheritem.package_file or ''
                    lesson.delete()
            except:
                pass
                    
        except Exception as e:
            pass
        return Response(status=status.HTTP_200_OK)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view([ 'DELETE', ])
@authentication_classes([BasicAuthenticationNoChallenge, TokenAuthentication,])
def deleteunusedcategories(request):
    if request:

        categories = Category.objects.all()
        for category in categories:
            try:
                if(category): #need to check as we can delete a parent, in this loop, which will cascade and this may be its no longer existant child
                    can_delete = True
                    childIDs = category.all_my_children()
                    for childID in childIDs:
                        if Category.objects.get(pk=childID).contentitem_set.all().count() > 0:
                            can_delete = False
                    try:
                        if can_delete:
                            category.delete()
                        else:
                            pass
                    except Exception as e:
                        #categories are protected elsewhere so wont delete if non empty.
                        pass
            except Category.DoesNotExist as e:
                pass
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view([ 'POST', ])
def checkteachercontent(request):
    teacherPackages = Package.objects.filter(preloaded=False)
    teacheritems = ContentItem.objects.filter(uploaded=True)
    lessons = TeacherGroup.objects.all()
    hascontent = (teacherPackages.count() > 0 or teacheritems.count() > 0 or lessons.count() > 0)
    return Response({ 'hasdata': hascontent }, status=status.HTTP_200_OK)

@api_view([ 'POST', ])
def checkcategories(request):
    cats = Category.objects.all()
    hascats = False
    can_delete = False

    if cats.count() > 0:
        for category in cats:
            if(category):
                can_delete = True
                childIDs = category.all_my_children()
                for childID in childIDs:
                    if Category.objects.get(pk=childID).contentitem_set.all().count() > 0:
                        can_delete = False

            if category.contentitem_set.all().count() == 0 and can_delete:
                hascats = True
                break
    return Response({ 'hasdata': hascats }, status=status.HTTP_200_OK)

import os
import shutil
import zipfile
from distutils.version import StrictVersion
import subprocess

#cant use this lookup as the gettext does not update if there is a language change, must use inline
'''
PATCH_ERROR = {
    'upload_error' : _('There was a problem uploading the file.'),
    'io_error': _('There was a problem with the file.'),
    'patch_less': _('Update version must be greater than the current version.\nPlease try again.'),
    'patch_equal': _('Update version must be greater than the current version.\nPlease try again.'),
    'invalid_patch': _('Invalid update file.\nPlease try again.')
}
'''

UNPATCHED_VERSION = '1.7.11' # this and anything previous
ZIP_PASSWORD = 'c*x4kd@qp6&8cgpa'
#ZIP_PASSWORD = 'password'
ZIP_ARCHIVE_NAME = 'data.zip'

'''
Patch is a password protected zip archive containing a second zip file named 'data.zip'
protected with the same password (for file obfuscation purposes)
At the root of 'data.zip' there should be an easyconnect folder all patch content is
relative to this folder on the device.
The root of 'data.zip' also contains a 'version.txt' file containing a single line with the version
number of the patch in x.y.z format.

patch.zip       (password)
    data.zip    (password)
        easyconnect/
            contentimport/
                migrations/
                    __init__.py
                    0001_initial.py
                    .
                    .
                    000N_auto__description.py
                models.py
            anyotherfolders/
        version.txt
'''

class Patch(APIView):
    def post(self, request, *args, **kwargs):
        if not 'content_file' in request.FILES:
            return Response({ 'message': _('There was a problem uploading the file.') }, status=status.HTTP_400_BAD_REQUEST)
        new_file = request.FILES['content_file']
        save_dir = PATCH_UPLOAD_DIR
        fs = FileSystemStorage(location=save_dir)
        if fs.exists(new_file.name):
            try:
                fs.delete(new_file.name)
            except Exception as e:
                return Response({ 'message': _('There was a problem with the file.') }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        content_file = fs.save(new_file.name, new_file)    

        try:
            shutil.rmtree(PATCH_UPPER_EXTRACT_DIR)
            shutil.rmtree(PATCH_EXTRACT_DIR)
        except:
            pass
        try:
            # extract top level zip archive
            with zipfile.ZipFile(save_dir + new_file.name, 'r') as patch:
                patch.extractall(PATCH_UPPER_EXTRACT_DIR, pwd=ZIP_PASSWORD)
            # extract lower level - actual content
            with zipfile.ZipFile(PATCH_UPPER_EXTRACT_DIR + ZIP_ARCHIVE_NAME, 'r') as patch:
                patch.extractall(PATCH_EXTRACT_DIR, pwd=ZIP_PASSWORD)
        except Exception as e:
            return Response({ 'message': _('Invalid update file.\nPlease try again.') }, status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            if self.patchVersionComp() < self.systemVersionComp():
                return Response({ 'message': _('Update version must be greater than the current version.\nPlease try again.') }, status=status.HTTP_406_NOT_ACCEPTABLE)
            elif self.patchVersionComp() == self.systemVersionComp():
                return Response({ 'message': _('Update version must be greater than the current version.\nPlease try again.') }, status=status.HTTP_406_NOT_ACCEPTABLE)
            elif self.patchVersionComp() > self.systemVersionComp():
                # TODO: backup database
                patch_version = self.getPatchVersion() # get version now, as fill will be gone once applied
                self.applyPatch()
                # update the version number in the database
                hide_lib_setting, created = SiteSetting.objects.get_or_create(name="ch_version", defaults={'value':patch_version})
                if not created:
                    hide_lib_setting.value = patch_version
                    hide_lib_setting.save()
                os.system('shutdown -r now') # reboot to apply migrations
                return Response({ 'message': 'restarting' }, status=status.HTTP_200_OK) # return (only if reboot using timeout)
        except Exception as e:
            return Response({ 'message': _('Invalid update file.\nPlease try again.') }, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    def patchVersionComp(self):
        return StrictVersion(self.getPatchVersion())

    def systemVersionComp(self):
        hide_lib_setting, created = SiteSetting.objects.get_or_create(name="ch_version", defaults={'value':UNPATCHED_VERSION})
        return StrictVersion(hide_lib_setting.value)

    def getPatchVersion(self):
        f = open(PATCH_EXTRACT_DIR + 'version.txt')
        return f.readline()

    def applyPatch(self):
        for src_dir, dirs, files in os.walk(PATCH_EXTRACT_DIR):
            dst_dir = src_dir.replace(PATCH_EXTRACT_DIR, PATCH_APPLY_DIR)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.move(src_file, dst_dir)

class TileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Tiles to be viewed or edited.
    """
    queryset = Tile.objects.all()
    serializer_class = TileSerializer
    ordering = ('display_order',)
    authentication_classes = (BasicAuthenticationNoChallenge, TokenAuthentication,)

    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('hidden', 'read_only', 'teacher_tile',)
    ordering_fields = ('display_order',)

    '''
    def get_queryset(self):
        queryset = Tile.objects.all()
        dict = {
            'Lesson Planner': _('Lesson Planner'),
            'Device Settings': _('Device Settings'),
            'Software Update': _('Software Update'),
            'Add Tile': _('Add Tile'),
        }
        for entry in dict:
            a = dict[entry].encode("utf8")
            queryset.filter(title=entry, read_only=True).update(title=a)
        return queryset
    '''

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            if not self.pre_save(serializer.object):
                return Response({}, status=status.HTTP_201_CREATED)# For IMS
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    
    def pre_save(self, obj):
        if self.request.method == 'POST':
            last_item = Tile.objects.all().aggregate(Max('display_order'))
            obj.display_order = last_item['display_order__max'] + 1
            obj.icon = icon_upload_handler(self.request)
            return True

    def get_success_headers(self, data):
        try:
            return {'Location': ''}
        except (TypeError, KeyError):
            return {}

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method == 'PUT':
            serializer_class = TileSerializerPut
        elif self.request.method == 'GET':
            serializer_class = TileSerializerTranslate_GetOnly
        return serializer_class

    '''
    Rest Delete
    '''
    def destroy(self, request, *args, **kwargs):
        exists = self.get_object()
        error = { 'status': 'error' }
        try:
            if exists and not exists.read_only:
                path = exists.storage_folder
                icon_path = exists.icon.path
                icon_path = icon_path.replace('media\\media', 'media') #hack to remove double media folder reference from icon path
                icon_path = icon_path.replace('media/media', 'media') #hack to remove double media folder reference from icon path
                if path.startswith(MEDIA_URL + PRELOAD_CONTENT_DIR): #prevent malicious access elsewhere in filesystem
                    path = path.replace(MEDIA_URL, MEDIA_ROOT)
                    try:
                        shutil.rmtree(path)
                    except:
                        #fail silently as this may not be a valid file path and we arent doing anything with the response.
                        pass
                
                #delete the icon manually (required django 1.3+ apparently)
                try:
                    os.remove(icon_path)
                except:
                    pass


                exists.delete()
                return Response({'status':'success'}, status=status.HTTP_200_OK)
            else:
                error['message'] = 'Tile does not exist or cannot be deleted'
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error['message'] = 'An error has occured while attempting to delete the tile'
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status':'success'}, status=status.HTTP_200_OK)

#Aidan added this class as the update in the TileViewSet kept stripping the title and url fields from the PUT request
class UpdateTile(APIView):
    authentication_classes = (BasicAuthenticationNoChallenge, TokenAuthentication,)

    def post(self,  request, *args, **kwargs):
        tileid = request.DATA["id"]
        if tileid:
            tile = Tile.objects.get(pk=int(tileid))
            try:
                tile.title = request.DATA["title"]
                tile.url_string = request.DATA["url_string"]
                tile.teacher_tile = request.DATA["teacher_tile"] == u"true"
                tile.hidden = request.DATA["hidden"] == u"true"

                try :
                    icon = request.DATA["icon"]
                    #no need to update icon if it is part of the data as it can only be changed by file selection
                except Exception:
                    try:
                        tile.icon = icon_upload_handler(self.request)
                    except Exception:
                        if "icon_path" in request.DATA:
                            #MPT supplying path to icon
                            #get the icon
                            mpt_icon_path = request.DATA["icon_path"]
                            mpt_root, mpt_filename = os.path.split(mpt_icon_path)
                            fileSize = get_file_size(mpt_icon_path)
                            save_dir = getSaveLocation(fileSize, MEDIA_ROOT + ICONS_DIR)
                            if isThereEnoughSpace(fileSize, save_dir):
                                fs = FileSystemStorage(location=save_dir)
                                #copy the icon            
                                if fs.exists(mpt_filename):
                                    mpt_filename = fs.get_available_name(mpt_filename)
                                with open(mpt_icon_path, 'rb') as file_obj:
                                    fs.save(mpt_filename, file_obj)
                                tile.icon = getMediaURL(save_dir) + mpt_filename
                            else:
                                return Response({ "error" :"Insufficient HDD space available" }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

                tile.save()
                headers = self.get_success_headers(tile)
                #return Response(json.JSONEncoder.default(self, tile), status=status.HTTP_200_OK, headers=headers)
                return Response({'status': 'success', 'message': 'done'}, status=status.HTTP_200_OK, headers=headers)
            except Exception:
                return Response({ "error" :"error saving tile" }, status=status.HTTP_400_BAD_REQUEST)
        else :
            return Response({ "error" :"bad_data" }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_success_headers(self, data):
        try:
            return {'Location': ''}
        except (TypeError, KeyError):
            return {}

class ReorderTiles(APIView):
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data.get('ids'):
            idlist = in_data['ids']
            for index, id in enumerate(idlist):
                tile = Tile.objects.get(pk=id)
                tile.display_order = index
                tile.save()
        return Response(status=status.HTTP_200_OK)

class CleanupTiles(APIView):
    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)
        if in_data.get('storage_folder'):
            path = in_data['storage_folder']
            if path.startswith(MEDIA_URL + PRELOAD_CONTENT_DIR): #prevent malicious access elsewhere in filesystem
                path = path.replace(MEDIA_URL, MEDIA_ROOT)
                try:
                    shutil.rmtree(path)
                except:
                    #fail silently as this may not be a valid file path and we arent doing anything with the response.
                    pass
        return Response(status=status.HTTP_200_OK)

class MPT_Tile_Path(APIView):
    '''
    MPT accept a path on device for icon & tile metadata.
    '''
    authentication_classes = (BasicAuthenticationNoChallenge,)

    def post(self, request, *args, **kwargs):
        in_data = json.loads(request.body)

        if all (required_keys in in_data for required_keys in ('title', 'icon', 'url_string')):
            try:
                #check duplicate name
                duplicate = False
                if Tile.objects.filter(title__iexact=in_data['title']):
                    return Response({'status': 'error', 'message': 'Title already exists.'}, status=status.HTTP_400_BAD_REQUEST)

                
                #get the site zip file
                site = site = type('obj', (object,), { 'micrositeURL': '', 'storageLocation': ''})
                if 'zippath' in in_data:
                    try:
                        mpt_zip_path = in_data['zippath']
                        site = Importer(mpt_zip_path, copy_to_upload=True, metadata={}, isMicrosite=True)
                        if site.outOfSpaceError:
                            return Response({'status': 'error', 'message': 'Insufficient HDD space available'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
 
                    except Exception as e:
                        return Response({'status': 'error', 'message': 'A file error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                #get the icon
                mpt_icon_path = in_data['icon']
                mpt_root, mpt_filename = os.path.split(mpt_icon_path)
                fileSize = get_file_size(mpt_icon_path)
                save_dir = getSaveLocation(fileSize, MEDIA_ROOT + ICONS_DIR)
                fs = FileSystemStorage(location=save_dir)

                if isThereEnoughSpace(fileSize, save_dir):
                    #copy the icon            
                    if fs.exists(mpt_filename):
                        mpt_filename = fs.get_available_name(mpt_filename)
                    with open(mpt_icon_path, 'rb') as file_obj:
                        fs.save(mpt_filename, file_obj)

                    last_item = Tile.objects.all().aggregate(Max('display_order'))
                    display_order = last_item['display_order__max'] + 1

                    build_url = ''
                    if site.storageLocation:
                        build_url = site.storageLocation + '/' + in_data['url_string']
                    else:
                        build_url = in_data['url_string']

                    newTile = Tile(
                        title = in_data['title'],
                        #icon = MEDIA_URL + ICONS_DIR + mpt_filename,
                        icon = getMediaURL(save_dir) + mpt_filename,
                        url_string = build_url,
                        url_target = '_blank',#in_data['target'] if 'target' in in_data else '_blank',
                        display_order = display_order,
                        teacher_tile = in_data['teacher_tile'] if 'teacher_tile' in in_data else False,
                        hidden = in_data['hidden'] if 'hidden' in in_data else False,
                        read_only = False,
                        storage_folder = site.storageLocation
                        )
                    newTile.save(force_insert=True)

                    return Response({'status': 'success', 'message': 'done'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'message': 'Insufficient HDD space available.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                    
            except Exception as e:
                return Response({'status': 'error', 'message': 'Internal Server Error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': 'error', 'message': 'Bad Request: Missing required parameters.'}, status=status.HTTP_400_BAD_REQUEST)


from django.conf import settings
DATABASES = getattr(settings, 'DATABASES', None)
BACKUPDIR = getattr(settings, 'BACKUPDIR', None)

from easyconnect.database_maintenance import restore_database
from easyconnect.startup_database import init_database

@api_view(['GET',])
def restoredatabase(request):    
    if os.path.isfile(DATABASES['default']['NAME']):
        dbname = os.path.basename(DATABASES['default']['NAME'])

        if os.path.isfile(os.path.join(BACKUPDIR, dbname)):
            try:
                hw_api = EasyconnectApApi()
                hw_api.restore_db()
		os.system('shutdown -r now')
                return Response({ 'message': 'restarting' }, status=status.HTTP_200_OK) 
            except Exception as e:
                return Response({'status': 'error', 'message': 'Internal Server Error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': 'error', 'message': 'Internal Server Error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'status': 'error', 'message': 'Internal Server Error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from time import strftime, gmtime
@api_view(['GET',])
def latestdatabase(request):
    BACKUPDIR = getattr(settings, 'BACKUPDIR', None)
    dbname = os.path.basename(DATABASES['default']['NAME'])
    backedupDatabase = os.path.join(BACKUPDIR, dbname);
    if os.path.isfile(backedupDatabase):
        return Response({ 'date' : strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime(os.path.getmtime(backedupDatabase)))})
    return Response({ 'date' : ''})