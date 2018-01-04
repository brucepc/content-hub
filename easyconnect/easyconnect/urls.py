from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic import TemplateView
from spa.views import TemplateViewTrans

from browse.views import ContentItemList, ContentItemDetail, ContentItemEdit, ContentItemDelete, filter_view, lesson_json, category_children_json, toggle_view, toggle_library, TeacherGroupDetail, lesson_detail, home, contentitem_detail, contentitem_frame, toggle_internet

from contentimport.views import usb_response, usb_file_select, usb_import

from django.conf import settings
from django.conf.urls.static import static

from easyconnect.settings import js_info_dict #javascript translation library

from rest_framework import routers
from rest import views
from rest_framework import authtoken

router = routers.DefaultRouter()
router.register(r'contentitems', views.ContentItemViewSet)
router.register(r'ie9contentitems', views.IE9_ContentItemViewSet)

router.register(r'categories', views.CategoryViewSet, 'categories')
router.register(r'categorytree', views.CategoryTree)

router.register(r'tags', views.TagViewSet)
router.register(r'lessons', views.TeacherGroupViewSet)

router.register(r'packages', views.PackageViewSet, 'packages')

router.register(r'tiles', views.TileViewSet, 'tiles')

handler404 = 'spa.views.handler404' 

# MPT explicit viewset url mappings
from rest.views import PackageViewSet, TileViewSet
mpt_package_list = PackageViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

mpt_package_detail = PackageViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

mpt_tile_list = TileViewSet.as_view({
    'get': 'list'
})
mpt_tile_detail = TileViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})
    

urlpatterns = patterns('',

    url(r'^rest/', include(router.urls)),
    url(r'^rest/auth/', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^rest/tokenauth/', views.AuthView.as_view(), name='authenticate'),

    # MPT url mappings
    url(r'^rest/mpt/packages/$', mpt_package_list, name='mpt_package_list'),
    url(r'^rest/mpt/packages/(?P<pk>[0-9]+)/$', mpt_package_detail, name='mpt_package_detail'),
    url(r'^rest/mpt/packagepath/', views.MPT_Package_Path.as_view(), name='mpt_package_path'),
    url(r'^rest/mpt/teachercontent/', 'rest.views.deleteteachercontent', name='mpt_deleteteachercontent'),
    url(r'^rest/mpt/categories/', 'rest.views.deleteunusedcategories', name='mpt_deleteunusedcategories'),

    url(r'^rest/mpt/tiles/$', mpt_tile_list, name='mpt_tile_list'),
    url(r'^rest/mpt/tiles/(?P<pk>[0-9]+)/$', mpt_tile_detail, name='mpt_tile_detail'),
    url(r'^rest/mpt/tilespath/', views.MPT_Tile_Path.as_view(), name='mpt_tile_path'),
    url(r'^rest/mpt/edittile/', views.UpdateTile.as_view(), name='mpt_tile_edit'),

    url(r'^rest/search/lessons/$', views.SearchView_Lessons.as_view(), name='search-lessons'),
    url(r'^rest/search/contentitems/$', views.SearchView_ContentItems.as_view(), name='search-contentitems'),

    url(r'^rest/settings/library/', views.Settings_Library.as_view(), name='settings_library'),
    url(r'^rest/settings/toggleviewtype/', views.Settings_update_session_viewtype.as_view(), name='update_session_viewtype'),
    
    url(r'^rest/settings/internet/', views.Settings_Internet.as_view(), name='settings_internet'),
    url(r'^rest/settings/ssid/', views.Settings_SSID.as_view(), name='settings_ssid'),
    url(r'^rest/settings/resetteacheraccount/', views.Settings_ResetTeacher.as_view(), name='settings_resetteacheraccount'),
    url(r'^rest/settings/changepassword/', views.Settings_CHANGEPASSWORD.as_view(), name='settings_changepassword'),

    url(r'^rest/settings/remotemanagement/', views.Settings_RemoteManagement.as_view(), name='settings_remotemanagement'),
 # Aidan Commented out code below as per request from Bun 01-06-16
    #url(r'^rest/settings/study/', views.Settings_Study.as_view(), name='settings_study'),
    url(r'^rest/settings/capversion/', views.Settings_DeviceVersion.as_view(), name='settings_deviceversion'),


    url(r'^rest/bulkdelete/', views.ContentItemBulkDelete.as_view(), name='bulk_delete'),
    url(r'^rest/bulkdeletepackage/', views.PackageBulkDelete.as_view(), name='bulk_delete_package'),
    url(r'^rest/patch/', views.Patch.as_view(), name='patch_system'),
    url(r'^rest/reordertiles/', views.ReorderTiles.as_view(), name='reorder_tiles'),
    url(r'^rest/cleanuptiles/', views.CleanupTiles.as_view(), name='cleanup_tiles'),
    url(r'^rest/updatetile/', views.UpdateTile.as_view(), name='update_tile'),

    #admin content management
    url(r'^rest/contentmanagement/deleteteachercontent/', 'rest.views.deleteteachercontent', name='deleteteachercontent'),
    url(r'^rest/contentmanagement/deleteunusedcategories/', 'rest.views.deleteunusedcategories', name='deleteunusedcategories'),

    url(r'^rest/contentmanagement/checkteachercontent/', 'rest.views.checkteachercontent', name='checkteachercontent'),
    url(r'^rest/contentmanagement/checkcategories/', 'rest.views.checkcategories', name='checkcategories'),


    # handler to poll upload status
    url(r'^rest/pollupload/', 'rest.UploadProgressCachedHandler.upload_progress', name='package_upload_progress'),
    url(r'^rest/poll_state/', 'rest.views.package_processing_progress', name='package_processing_progress'),
    url(r'^rest/cancelupload/', 'rest.UploadProgressCachedHandler.cancel_upload', name='package_cancel_upload'),

    #url(r'^rest/usb_util/root', views.USB_Util_Root.as_view(), name='usb_util_root'),
    url(r'^rest/usb_util/list/', views.USB_Util_Dir.as_view(), name='usb_util_dir'),
    url(r'^rest/usb_util/upload/', views.USB_Util_Upload.as_view(), name='usb_upload'),
    
    #get date of latest restore
    url(r'^rest/database/latest', views.latestdatabase, name='latestdatabase'),

    #Restore previously backed up database
    url(r'^rest/database/restore', views.restoredatabase, name='restoredatabase'),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),

    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict), #translation catalog for .js files

    #url(r'^angularviews/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'spa/templates/views/'}),
    #url(r'^angularpartials/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'spa/templates/partials/'}),

    url(r'^angularpartials/categoryselect.html', TemplateView.as_view(template_name='partials/categoryselect.html')),
    url(r'^angularpartials/categorytree.html', TemplateView.as_view(template_name='partials/categorytree.html')),
    url(r'^angularpartials/contentitems.html', TemplateView.as_view(template_name='partials/contentitems.html')),
    url(r'^angularpartials/lessons.html', TemplateView.as_view(template_name='partials/lessons.html')),
    url(r'^angularpartials/pager.html', TemplateView.as_view(template_name='partials/pager.html')),
    url(r'^angularpartials/tagcloud.html', TemplateView.as_view(template_name='partials/tagcloud.html')),
    url(r'^angularpartials/sort.html', TemplateView.as_view(template_name='partials/sort.html')),
    url(r'^angularpartials/busytemplate.html', TemplateView.as_view(template_name='partials/busytemplate.html')),

    url(r'^angularviews/categories.html', TemplateView.as_view(template_name='views/categories.html')),
    url(r'^angularviews/help.html', TemplateViewTrans.as_view(template_name='views/help.html', help_type='teacher')),
    url(r'^angularviews/student_help.html', TemplateViewTrans.as_view(template_name='views/student_help.html', help_type='student')),
    url(r'^angularviews/admin_help.html', TemplateViewTrans.as_view(template_name='views/admin_help.html', help_type='admin')),
    url(r'^angularviews/home.html', TemplateView.as_view(template_name='views/home.html')),
    url(r'^angularviews/lesson_detail.html', TemplateView.as_view(template_name='views/lesson_detail.html')),
    url(r'^angularviews/lessons.html', TemplateView.as_view(template_name='views/lessons.html')),
    url(r'^angularviews/library.html', TemplateView.as_view(template_name='views/library.html')),
    url(r'^angularviews/login.html', TemplateView.as_view(template_name='views/login.html')),
    url(r'^angularviews/settings.html', TemplateView.as_view(template_name='views/settings.html')),
    url(r'^angularviews/sidebar.html', TemplateView.as_view(template_name='views/sidebar.html')),
    url(r'^angularviews/tags.html', TemplateView.as_view(template_name='views/tags.html')),
    url(r'^angularviews/terms.html', TemplateView.as_view(template_name='views/terms.html')),
    url(r'^angularviews/upload.html', TemplateView.as_view(template_name='views/upload.html')),
    url(r'^angularviews/uploadIE9.html', TemplateView.as_view(template_name='views/uploadIE9.html')),
    url(r'^angularviews/usb.html', TemplateView.as_view(template_name='views/usb.html')),

    url(r'^angularviews/preload-upload.html', TemplateView.as_view(template_name='views/preload-upload.html')),
    url(r'^angularviews/preload-usb.html', TemplateView.as_view(template_name='views/preload-usb.html')),

    url(r'^angularpartials/hub/tile.html', TemplateView.as_view(template_name='hub/partials/tile.html')),
    url(r'^angularviews/hub/home.html', TemplateView.as_view(template_name='hub/views/home.html')),
    url(r'^angularviews/hub/404.html', TemplateView.as_view(template_name='hub/views/404.html')),

    url(r'^angularpartials/teacheradmin/noauth.html', TemplateView.as_view(template_name='teacheradmin/partials/noauth.html')),
    url(r'^angularviews/teacheradmin/home.html', TemplateView.as_view(template_name='teacheradmin/views/home.html')),
    url(r'^angularviews/teacheradmin/changepass.html', TemplateView.as_view(template_name='teacheradmin/views/changepass.html')),
    url(r'^angularviews/teacheradmin/preloadedcontent.html', TemplateView.as_view(template_name='teacheradmin/views/preloadedcontent.html')),
    url(r'^angularviews/teacheradmin/upload.html', TemplateView.as_view(template_name='teacheradmin/views/upload.html')),
    url(r'^angularviews/teacheradmin/usb.html', TemplateView.as_view(template_name='teacheradmin/views/usb.html')),

    url(r'^angularviews/updater/home.html', TemplateView.as_view(template_name='updater/views/home.html')),

    url(r'^angularviews/branding.css', TemplateView.as_view(template_name='branding.css')),
)

#usb management
urlpatterns += patterns('',
    url(r'^usb/$', usb_file_select, name='usb-file'),
    url(r'^usb/import/$', usb_import, name='usb-import'),
    url(r'^usb/json/$', usb_response, name='usb-response'),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))

if not settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )

urlpatterns += patterns('',
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /*", mimetype="text/plain")),
)

urlpatterns += patterns('',
    #url(r'^admin/', include(admin.site.urls)), #uncomment to enable admin
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'browse/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^upload/$', 'browse.views.upload_file', name='upload'),
    url(r'^help/$', TemplateView.as_view(template_name="browse/help.html"), name='help'),
    url(r'^edit/(?P<id>\d+)/$', login_required(ContentItemEdit.as_view()), name='edit'),
    url(r'^delete/(?P<id>\d+)/$', login_required(ContentItemDelete.as_view()), name='delete'),
    url(r'^hide/(?P<id>\d+)/$', 'browse.views.hide_item', name='hide'),
    url(r'^unhide/(?P<id>\d+)/$', 'browse.views.unhide_item', name='unhide'),
    url(r'^feature/(?P<id>\d+)/$', 'browse.views.feature_item', name='feature'),
    url(r'^add_to_group/(?P<id>\d+)/$', 'browse.views.add_item_to_group', name='add-item-to-group'),
    url(r'^unfeature/(?P<id>\d+)/$', 'browse.views.unfeature_item', name='unfeature'),
    url(r'^add/(?P<model_name>\w+)/?$', 'browse.views.add_new_model', name="add"),
    url(r'^manage/', include('catalogue.urls')),
)



urlpatterns += patterns('',
    url(r'^lessons/(?P<lesson_id>\d+)/$', lesson_detail, name='group-detail'),
    url(r'^lessons/json/$', lesson_json, name='lessons-json'),
    url(r'^library/cat_children/json/$', category_children_json, name='category-children-json'),
    url(r'^library/$', filter_view, {'template': 'browse/library.html'}, name='library'),
    url(r'^library/(?P<source>.+)/$', filter_view, {'template': 'browse/library.html'}, name='library'),
    url(r'^lessons/$', filter_view, {'template': 'browse/lessons.html'}, name='lessons'),
    url(r'^toggle/$', toggle_view, name='toggle-view'),
    url(r'^togglelibrary/$', toggle_library, name='toggle-library'),
    url(r'^togglenet/$', toggle_internet, name='toggle-net'),
    url(r'^contentframe/$', contentitem_frame, name='contentitem-frame'),
)

# need to match before categories # TODO: specifically check for non-numbers
urlpatterns += patterns('',
    url(r'^detail/$', contentitem_detail, name='detail'), # or be at the start with nothing after
)

from spa.views import spahome
from hub.views import hubhome
from teacheradmin.views import teacheradminhome
from updater.views import updaterhome
from spa.views import Test #dispatchAdminView

urlpatterns += patterns('',
    url(r'^update/$', updaterhome , name='indexofupdater'),
    url(r'^devicesettings/$', teacheradminhome, name='indexofteacheradmin'),
    url(r'^lessonplanner/$', Test.as_view(), name='index'),
    url(r'^$', hubhome, name='index'),
)