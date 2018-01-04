from django import forms
from contentimport.models import ContentItem, Tag
from browse.widgets import SelectWithPopUp

class UploadForm(forms.ModelForm):

	class Meta:
		model = ContentItem
		fields = ['title', 'description', 'content_file']
		widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'rows': 7, 'placeholder': 'Description'}),
            #'tags': SelectWithPopUp,
        }

class UpdateForm(forms.ModelForm):

    class Meta:
        model = ContentItem
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'rows': 7, 'placeholder': 'Description'}),
            #'tags': SelectWithPopUp,
        }