'''
from __future__ import unicode_literals

import logging

from django.db import models

from haystack import signals
from haystack.exceptions import NotHandled

from contentimport.models import ContentItem, Category, Tag, TeacherGroup

class ContentItemOnlySignalProcessor(signals.RealtimeSignalProcessor):
    def setup(self):
        """
        A hook for setting up anything necessary for
        ``handle_save/handle_delete`` to be executed.

        Default behavior is to do nothing (``pass``).
        """
        #items
        models.signals.post_save.connect(self.handle_save, sender=ContentItem)
        models.signals.post_delete.connect(self.handle_delete, sender=ContentItem)

        #models.signals.m2m_changed.connect(self.update_m2mC, sender=ContentItem)
        #models.signals.m2m_changed.connect(self.handle_save, sender=ContentItem.categories.through)
        #models.signals.m2m_changed.connect(self.handle_save, sender=ContentItem.tags.through)

        #lessons
        models.signals.post_save.connect(self.handle_save, sender=TeacherGroup)
        models.signals.post_delete.connect(self.handle_delete, sender=TeacherGroup)

        #models.signals.pre_delete.connect(self.handle_m2m_delete, sender=Category)
        #models.signals.pre_delete.connect(self.handle_save, sender=Category)

        #models.signals.pre_delete.connect(self.handle_m2m_delete, sender=Tag)

        
        #models.signals.post_save.connect(self.handle_save, sender=Tag)

    def teardown(self):
        """
        A hook for tearing down anything necessary for
        ``handle_save/handle_delete`` to no longer be executed.

        Default behavior is to do nothing (``pass``).
        """
        #items
        models.signals.post_save.disconnect(self.handle_save, sender=ContentItem)
        models.signals.post_delete.disconnect(self.handle_delete, sender=ContentItem)

        #models.signals.m2m_changed.connect(self.update_m2mC, sender=ContentItem)
        #models.signals.m2m_changed.disconnect(self.handle_save, sender=ContentItem.categories.through)
        #models.signals.m2m_changed.disconnect(self.handle_save, sender=ContentItem.tags.through)

        #lessons
        models.signals.post_save.disconnect(self.handle_save, sender=TeacherGroup)
        models.signals.post_delete.disconnect(self.handle_delete, sender=TeacherGroup)

        #models.signals.pre_delete.disconnect(self.handle_m2m_delete, sender=Category)
        #models.signals.pre_delete.disconnect(self.handle_save, sender=Category)

        #models.signals.pre_delete.disconnect(self.handle_m2m_delete, sender=Tag)
        #models.signals.post_save.disconnect(self.handle_save, sender=Tag)

    def handle_save(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        dont_index = getattr(instance, '_dont_index', False)
        if dont_index:
            print('dont_index is TRUE')
        else:
            using_backends = self.connection_router.for_write(instance=instance)
            for using in using_backends:
                try:
                    #index = self.connections[using].get_unified_index().get_index(instance.__class__) # we had to change this line slightly to track changes to m2m fields
                    index = self.connections[using].get_unified_index().get_index(sender)
                    index.update_object(instance, using=using)
                except NotHandled:
                    pass


'''