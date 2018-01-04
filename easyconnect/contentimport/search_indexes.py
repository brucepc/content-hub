'''
import datetime

from django.conf import settings

from haystack import indexes

from contentimport.models import ContentItem, TeacherGroup

UPLOAD_CONTENT_DIR = getattr(settings, 'UPLOAD_CONTENT_DIR', None)
MEDIA_URL = getattr(settings, 'MEDIA_URL', None)

class ContentItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description', null=True)
    hidden = indexes.BooleanField(model_attr='hidden')
    categories = indexes.MultiValueField()
    tags = indexes.MultiValueField()
    autocomplete = indexes.EdgeNgramField(model_attr='title')
    date_added = indexes.DateTimeField(model_attr='date_added')
    uploaded = indexes.BooleanField(model_attr='uploaded')

    def get_model(self):
        return ContentItem

    def get_updated_field(self):
        return "updated"

    def prepare_categories(self,object):
        return [category.pk for category in object.categories.all()]

    def prepare_tags(self,object):
        return [tag.pk for tag in object.tags.all()]

class TeacherGroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    autocomplete = indexes.EdgeNgramField(model_attr='title')

    def get_model(self):
        return TeacherGroup

    def get_updated_field(self):
        return "updated"

'''