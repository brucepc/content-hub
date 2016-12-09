import autocomplete_light
from contentimport.models import ContentItem, TeacherGroup, models


class ContentItemAutocomplete(autocomplete_light.AutocompleteModelBase):
    model = ContentItem
    '''
    def choice_label(self, choice):
       return ContentItem.objects.get(pk=choice.id).description
    '''

autocomplete_light.register(ContentItem, ContentItemAutocomplete,
    search_fields=['title', 'description'],
    choices=ContentItem.objects.all()
)


'''
autocomplete_light.register(ContentItem,
    search_fields=['title', 'description'],
    choices=ContentItem.objects.all()
)
'''

autocomplete_light.register(TeacherGroup,
    search_fields=['title'],
    choices=TeacherGroup.objects.all()
)