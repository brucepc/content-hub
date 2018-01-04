from django.forms import Form, ModelForm, ModelChoiceField, CharField, CheckboxSelectMultiple
from django.forms.widgets import Select

from contentimport.models import ContentItem, Category, TeacherGroup, Tag
    
class AddCategory(ModelForm):
    parent = ModelChoiceField(
        queryset=Category.objects.all(),
        widget=Select,
        label = 'Parent Category',
        empty_label = '- None -',
        required = False
    )
    class Meta:
        model = Category
        fields = ['name', 'parent']


class DeleteTag(ModelForm):
    tag_text = ModelChoiceField(
        queryset = Tag.objects.all(),
        widget = Select,
    )
    class Meta:
        model = Tag
        fields = ['tag_text']

class EditCategory(ModelForm):
    name = ModelChoiceField(
        queryset=Category.objects.all(),
        widget=Select,
    )
    new_name = CharField(max_length=100, required=True,)
    class Meta:
        model = Category
        fields = ['name', 'new_name']

class DeleteCategory(ModelForm):
    name = ModelChoiceField(
        queryset=Category.objects.all(),
        widget=Select,
    )
    class Meta:
        model = Category
        fields = ['name']

class AddGroup(ModelForm):
    class Meta:
        model = TeacherGroup
        fields = ['title']

class EditGroup(ModelForm):
    title = ModelChoiceField(
        queryset=TeacherGroup.objects.all(),
        widget=Select,
    )
    new_name = CharField(max_length=100, required=True,)
    class Meta:
        model = TeacherGroup
        fields = ['title']

class DeleteGroup(ModelForm):
    title = ModelChoiceField(
        queryset=TeacherGroup.objects.all(),
        widget=Select,
    )
    class Meta:
        model = TeacherGroup
        fields = ['title']

class AddContentItemToGroup(Form):
    members = ModelChoiceField(
        queryset=ContentItem.objects.all(),
        widget=CheckboxSelectMultiple,
        empty_label=None,
    )
    title = ModelChoiceField(
        queryset=TeacherGroup.objects.all(),
        widget=Select,
        empty_label=None,
    )
class GroupItems(Form):
    title = ModelChoiceField(
        queryset=TeacherGroup.objects.all(),
        widget=Select,
        empty_label=None,
    )
