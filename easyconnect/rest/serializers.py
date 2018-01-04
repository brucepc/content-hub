from contentimport.models import ContentItem, TeacherGroup, Category, Tag, TeacherGroup, TeacherGroupMembership, Package, PackageMembership, Tile
from rest_framework import serializers, pagination
from django.db.models import Count
from django.contrib.auth.models import User



class CategorySerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(required=False)
    uses = serializers.IntegerField(source='contentitem_set.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'uses', 'locked')


class CategoryTreeSerializer(serializers.ModelSerializer):
    uses = serializers.IntegerField(source='contentitem_set.count', read_only=True)
    text = serializers.CharField(source='name')

    def to_native(self, obj):
        #Add any self-referencing fields here
        if not self.fields.has_key('children'):
            self.fields['children'] = CategoryTreeSerializer(many=True)      
        return super(CategoryTreeSerializer,self).to_native(obj) 

    class Meta:
        model = Category
        fields = ('id', 'parent', 'text', 'name', 'uses', 'locked')


class TagSerializer(serializers.ModelSerializer):
    uses = serializers.IntegerField(source='contentitem_set.count', read_only=True)
    class Meta:
        model = Tag
        fields = ('id', 'text', 'score', 'uses', 'locked')

class TagSerializer_ForNested(serializers.ModelSerializer):
    #uses = serializers.IntegerField(source='contentitem_set.count', read_only=True)
    class Meta:
        model = Tag
        fields = ('id','text')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser')

# now only used in lesson listing
class ContentItemSerializer(serializers.ModelSerializer):
    tags = TagSerializer_ForNested(many=True)
    class Meta:
        model = ContentItem
        fields = ('id', 'title', 'description', 'content_file', 'file_size',
                  'mime_type', 'date_added', 'featured', 'hidden', 'identifier', 'updated',
                  'tags')

class ContentItemSerializer_IE9_Error(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = ('title', 'content_file')

class ContentItemSerializerPost(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = ('id', 'title', 'description', 'content_file', 'file_size',
                  'mime_type', 'date_added', 'featured', 'hidden', 'identifier', 'updated',
                  'tags', 'categories')

class ContentItemSerializerPut(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = ('id', 'title', 'description', 'featured', 'hidden', 'updated',
                  'tags', 'categories')

class ContentItemSerializerGet(serializers.ModelSerializer):
    tags = TagSerializer_ForNested(many=True)
    categories = CategorySerializer(many=True)
    class Meta:
        model = ContentItem
        fields = ('id', 'title', 'description', 'content_file', 'file_size', 'uploaded',
                  'mime_type', 'date_added', 'featured', 'hidden', 'identifier', 'updated',
                  'tags', 'categories')

class TeacherGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherGroup
        fields = ('id', 'title', 'featured', 'updated', 'members')

class TeacherGroupSerializerNested(serializers.ModelSerializer):
    members = ContentItemSerializer(source='members')
    class Meta:
        model = TeacherGroup
        fields = ('id', 'title', 'featured', 'updated', 'members')


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'package_file', 'date_added', 'filesize', 'title')

class TileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('id', 'title', 'icon', 'url_string', 'url_target', 'display_order', 'hidden', 'read_only', 'teacher_tile', 'updated', 'storage_folder')

class TileSerializerTranslate_GetOnly(serializers.ModelSerializer):
    title = serializers.Field(source='translate_title')
    class Meta:
        model = Tile
        fields = ('id', 'title', 'icon', 'url_string', 'url_target', 'display_order', 'hidden', 'read_only', 'teacher_tile', 'updated', 'storage_folder')

class TileSerializerPut(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('id', 'title', 'url_string', 'url_target', 'display_order', 'hidden', 'teacher_tile', 'updated')

        