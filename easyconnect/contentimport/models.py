import logging

from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)

MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', None)
UPLOAD_CONTENT_DIR = getattr(settings, 'UPLOAD_CONTENT_DIR', None)
ICONS_DIR = getattr(settings, 'ICONS_DIR', None)

fs = FileSystemStorage(location=MEDIA_ROOT)

class RemoteAPI(models.Model):
    title = models.CharField(max_length=20)
    title_hash = models.CharField(max_length=32, editable=False)
    url = models.URLField(max_length=600)
    username = models.CharField(max_length=20, blank=True, null=True)
    key = models.CharField(max_length=256, blank=True, null=True)
    resource_name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = "remote API"
        verbose_name_plural = "remote APIs"

class Notify(models.Model):
    """Must add one element from this model to have the option of turining on/off the log system  **could make it a fixture in the future** """

    justText = models.CharField(max_length=50) #a text to avoid the Unicode error
    notify = models.BooleanField('Show Notifications?', default=True)
    def __unicode__(self):
        return self.justText

class SiteSetting(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=256, blank=True, null=True)

    def __unicode__(self):
        return self.name
    
class Log(models.Model):
    LOG_TYPE = (('err', 'Error'), ('noti', 'Notification'))
    text = models.TextField()
    datetime = models.DateTimeField()
    logType = models.CharField(max_length=4,choices=LOG_TYPE)
    def __unicode__(self):
        return self.text

class Tag(models.Model):
    text = models.CharField(max_length=25)
    score = models.PositiveIntegerField(editable=False, default=0)
    locked = models.BooleanField(default=False)

    def __unicode__(self):
        return self.text

    def delete_if_empty_excluding(self, contentitem):
        """
        delete this tag if you've no contentitems bar 'contentitem'
        """
        if self.contentitem_set.exclude(pk=contentitem.id).count() == 0:
            self.delete()

        return

class Category(models.Model):
    name = models.CharField(max_length=100, blank=False)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True) # need to assign all parent categories to each item! Maybe!
    locked = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    '''
    class Meta:
        unique_together = ('name', 'parent')
    '''

    def delete_hierarchy_if_empty_excluding(self, contentitem):
        """
        true to its catchy name, this will delete this category if there's none of this contentitem associated and delete its parents if same, 
        going up the chain until they're all removed
        """
        if self.contentitem_set.exclude(title=contentitem).count() == 0:
            if self.parent is not None:
                self.parent.delete_hierarchy_if_empty_excluding(contentitem)
            self.delete()

        return

    def all_my_children(self):
        """
        return list of ids for all the children, children's children etc of this category
        """
        response = self.__children_all_the_way_down(self)

        return response

    def __children_all_the_way_down(self, category):
        """
        recursive function to list ids for all children of a category, check those children for their own children etc
        """
        children = Category.objects.filter(parent=category).order_by('id')

        child_list = [ category.pk ]
        child_list.extend(list(children.values_list('id', flat=True)))

        for child in children:
            child_list.extend(self.__children_all_the_way_down(child))

        return child_list

    def ancestors(self):
        parents = None
        try:
            dad = Category.objects.get(pk=self.parent.pk)
            parents = [ dad.name ]
        except:
            pass
        else:
            try:
                grandpa = Category.objects.get(pk=dad.parent.pk)
                parents.insert(0, grandpa.name)
            except:
                pass

        return parents

class Package(models.Model):
    """
    each Package representing one manifest from a zip package as it arrived
    """
    title = models.CharField(max_length=100, blank=True, editable=False, null=True)
    description = models.TextField(blank=True, editable=False, null=True)
    date_added = models.DateTimeField('date added', auto_now_add=True, editable=False)
    package_file = models.TextField(editable=False)
    identifier = models.CharField(max_length=200, blank=False, editable=False)
    version = models.CharField(max_length=200, blank=True, editable=False, null=True)
    file_hash = models.CharField(max_length=32, editable=False)
    preloaded = models.BooleanField(default=False)
    filesize = models.TextField(max_length=25, blank=True, editable=False, null=True)


    def __unicode__(self):
        return self.title

    class Meta:
        unique_together = ('package_file', 'identifier')

    def get_contentitems(self):
        return self.contentitem_set.all()

    def delete_if_empty_excluding(self, contentitem):
        """
        """
        if self.contentitem_set.exclude(title=contentitem).count() == 0:
            self.delete()

class ContentItem(models.Model):
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.FileField(upload_to=MEDIA_ROOT+UPLOAD_CONTENT_DIR, blank=True) # path and filename (media_root?)
    content_file = models.FileField('the content file', storage=fs, upload_to=UPLOAD_CONTENT_DIR) # path + filename for package, index page or individual file
    file_size = models.PositiveIntegerField('file size', editable=False)
    mime_type = models.CharField('mime type', max_length=50, editable=False, blank=True, null=True)
    date_added = models.DateTimeField('date added', auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)
    categories = models.ManyToManyField(Category, blank=True, null=False)
    packages = models.ManyToManyField(Package, through='PackageMembership', blank=True)
    file_hash = models.CharField(max_length=32, editable=False)
    featured = models.BooleanField('is this a featured file?', default=False)
    featured_start = models.DateTimeField(blank=True, null=True, default=None)
    featured_end = models.DateTimeField(blank=True, null=True, default=None)
    hidden = models.BooleanField('is this file hidden from the student view?', default=False)
    identifier = models.CharField(max_length=200, blank=True, null=True, editable=False)
    uploaded = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    #class Meta:
        #unique_together = ('content_file', 'identifier')

    def get_packages(self):
        return self.packagemembership_set.all()


class TeacherGroup(models.Model):
    title = models.CharField(max_length=100, blank=False)
    #members = models.ManyToManyField(ContentItem, through='TeacherGroupMembership', blank=True)
    members = models.ManyToManyField(ContentItem, blank=True)
    featured = models.BooleanField('is this a featured group?', default=False)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title


class TeacherGroupMembership(models.Model):
    item = models.ForeignKey(ContentItem)
    group = models.ForeignKey(TeacherGroup) # could be in more than one group, but might not be featured in all of them
    featured = models.BooleanField(default=False)
    featured_start = models.DateTimeField(blank=True, null=True, default=None)# featured within the group, but not neccessarily site-wide
    featured_end = models.DateTimeField(blank=True, null=True, default=None)

    def __unicode__(self):
        return self.group.title

    class Meta:
        unique_together = ('item', 'group')

class PackageMembership(models.Model):
    package = models.ForeignKey(Package)
    resource = models.ForeignKey(ContentItem)
    position = models.PositiveIntegerField(default=0, blank=False, editable=False)

from django.utils.translation import ugettext as _
class Tile(models.Model):
    title = models.CharField(max_length=100, blank=False)
    #icon = models.CharField(max_length=100, blank=False) #upload_to='tile_icons', null=True)
    url_string = models.CharField(max_length=300, blank=False)
    url_target = models.CharField(max_length=20, default='_blank')
    display_order = models.IntegerField(default=0)
    teacher_tile = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False) # one of the core 3
    updated = models.DateTimeField(auto_now=True)

    storage_folder = models.CharField(max_length=300, blank=False)
    icon = models.FileField('the icon file', storage=fs, upload_to=ICONS_DIR)

    def translate_title(self):
        if self.read_only:
            dict = {
                'Lesson Planner': _('Lesson Planner'),
                'Device Settings': _('Device Settings'),
                'Software Update': _('Software Update'),
                'Add Tile': _('Add Tile'),
            }
            if self.title in dict:
                return dict[self.title]
        return self.title

    def __unicode__(self):
        return self.title