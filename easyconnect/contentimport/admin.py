from django.contrib import admin
from contentimport.models import ContentItem, Category, Tag, Package, TeacherGroup, TeacherGroupMembership, Log, SiteSetting, RemoteAPI


class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_added', 'uploaded']

admin.site.register(ContentItem, ContentItemAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']

admin.site.register(Category, CategoryAdmin)

class TagAdmin(admin.ModelAdmin):
	list_display = ['text', 'score']

admin.site.register(Tag, TagAdmin)

class PackageAdmin(admin.ModelAdmin):
    list_display = ['id', 'package_file', 'identifier', 'version', 'title', 'date_added', 'description']

admin.site.register(Package, PackageAdmin)

class TeacherGroupAdmin(admin.ModelAdmin):
    list_display = ['title']

admin.site.register(TeacherGroup, TeacherGroupAdmin)

class TeacherGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['item', 'group', 'featured', 'featured_start', 'featured_end']

admin.site.register(TeacherGroupMembership, TeacherGroupMembershipAdmin)

admin.site.register(Log)

class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')

admin.site.register(SiteSetting)
admin.site.register(RemoteAPI)
