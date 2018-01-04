# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RemoteAPI'
        db.create_table(u'contentimport_remoteapi', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('title_hash', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=600)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('resource_name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'contentimport', ['RemoteAPI'])

        # Adding model 'Notify'
        db.create_table(u'contentimport_notify', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('justText', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('notify', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'contentimport', ['Notify'])

        # Adding model 'SiteSetting'
        db.create_table(u'contentimport_sitesetting', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal(u'contentimport', ['SiteSetting'])

        # Adding model 'Log'
        db.create_table(u'contentimport_log', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('logType', self.gf('django.db.models.fields.CharField')(max_length=4)),
        ))
        db.send_create_signal(u'contentimport', ['Log'])

        # Adding model 'Tag'
        db.create_table(u'contentimport_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('score', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'contentimport', ['Tag'])

        # Adding model 'Category'
        db.create_table(u'contentimport_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['contentimport.Category'])),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'contentimport', ['Category'])

        # Adding model 'Package'
        db.create_table(u'contentimport_package', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('package_file', self.gf('django.db.models.fields.TextField')()),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('file_hash', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('preloaded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('filesize', self.gf('django.db.models.fields.TextField')(max_length=25, null=True, blank=True)),
        ))
        db.send_create_signal(u'contentimport', ['Package'])

        # Adding unique constraint on 'Package', fields ['package_file', 'identifier']
        db.create_unique(u'contentimport_package', ['package_file', 'identifier'])

        # Adding model 'ContentItem'
        db.create_table(u'contentimport_contentitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('content_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('file_size', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('mime_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file_hash', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('featured_start', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('featured_end', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('uploaded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'contentimport', ['ContentItem'])

        # Adding M2M table for field tags on 'ContentItem'
        m2m_table_name = db.shorten_name(u'contentimport_contentitem_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('contentitem', models.ForeignKey(orm[u'contentimport.contentitem'], null=False)),
            ('tag', models.ForeignKey(orm[u'contentimport.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['contentitem_id', 'tag_id'])

        # Adding M2M table for field categories on 'ContentItem'
        m2m_table_name = db.shorten_name(u'contentimport_contentitem_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('contentitem', models.ForeignKey(orm[u'contentimport.contentitem'], null=False)),
            ('category', models.ForeignKey(orm[u'contentimport.category'], null=False))
        ))
        db.create_unique(m2m_table_name, ['contentitem_id', 'category_id'])

        # Adding model 'TeacherGroup'
        db.create_table(u'contentimport_teachergroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'contentimport', ['TeacherGroup'])

        # Adding M2M table for field members on 'TeacherGroup'
        m2m_table_name = db.shorten_name(u'contentimport_teachergroup_members')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('teachergroup', models.ForeignKey(orm[u'contentimport.teachergroup'], null=False)),
            ('contentitem', models.ForeignKey(orm[u'contentimport.contentitem'], null=False))
        ))
        db.create_unique(m2m_table_name, ['teachergroup_id', 'contentitem_id'])

        # Adding model 'TeacherGroupMembership'
        db.create_table(u'contentimport_teachergroupmembership', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contentimport.ContentItem'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contentimport.TeacherGroup'])),
            ('featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('featured_start', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('featured_end', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'contentimport', ['TeacherGroupMembership'])

        # Adding unique constraint on 'TeacherGroupMembership', fields ['item', 'group']
        db.create_unique(u'contentimport_teachergroupmembership', ['item_id', 'group_id'])

        # Adding model 'PackageMembership'
        db.create_table(u'contentimport_packagemembership', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contentimport.Package'])),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contentimport.ContentItem'])),
            ('position', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'contentimport', ['PackageMembership'])


    def backwards(self, orm):
        # Removing unique constraint on 'TeacherGroupMembership', fields ['item', 'group']
        db.delete_unique(u'contentimport_teachergroupmembership', ['item_id', 'group_id'])

        # Removing unique constraint on 'Package', fields ['package_file', 'identifier']
        db.delete_unique(u'contentimport_package', ['package_file', 'identifier'])

        # Deleting model 'RemoteAPI'
        db.delete_table(u'contentimport_remoteapi')

        # Deleting model 'Notify'
        db.delete_table(u'contentimport_notify')

        # Deleting model 'SiteSetting'
        db.delete_table(u'contentimport_sitesetting')

        # Deleting model 'Log'
        db.delete_table(u'contentimport_log')

        # Deleting model 'Tag'
        db.delete_table(u'contentimport_tag')

        # Deleting model 'Category'
        db.delete_table(u'contentimport_category')

        # Deleting model 'Package'
        db.delete_table(u'contentimport_package')

        # Deleting model 'ContentItem'
        db.delete_table(u'contentimport_contentitem')

        # Removing M2M table for field tags on 'ContentItem'
        db.delete_table(db.shorten_name(u'contentimport_contentitem_tags'))

        # Removing M2M table for field categories on 'ContentItem'
        db.delete_table(db.shorten_name(u'contentimport_contentitem_categories'))

        # Deleting model 'TeacherGroup'
        db.delete_table(u'contentimport_teachergroup')

        # Removing M2M table for field members on 'TeacherGroup'
        db.delete_table(db.shorten_name(u'contentimport_teachergroup_members'))

        # Deleting model 'TeacherGroupMembership'
        db.delete_table(u'contentimport_teachergroupmembership')

        # Deleting model 'PackageMembership'
        db.delete_table(u'contentimport_packagemembership')


    models = {
        u'contentimport.category': {
            'Meta': {'object_name': 'Category'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['contentimport.Category']"})
        },
        u'contentimport.contentitem': {
            'Meta': {'object_name': 'ContentItem'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contentimport.Category']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'featured_end': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'featured_start': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'file_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'file_size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'packages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contentimport.Package']", 'symmetrical': 'False', 'through': u"orm['contentimport.PackageMembership']", 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contentimport.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'contentimport.log': {
            'Meta': {'object_name': 'Log'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logType': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'contentimport.notify': {
            'Meta': {'object_name': 'Notify'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'justText': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'notify': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'contentimport.package': {
            'Meta': {'unique_together': "(('package_file', 'identifier'),)", 'object_name': 'Package'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'filesize': ('django.db.models.fields.TextField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'package_file': ('django.db.models.fields.TextField', [], {}),
            'preloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'contentimport.packagemembership': {
            'Meta': {'object_name': 'PackageMembership'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contentimport.Package']"}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contentimport.ContentItem']"})
        },
        u'contentimport.remoteapi': {
            'Meta': {'object_name': 'RemoteAPI'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'resource_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'title_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '600'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'contentimport.sitesetting': {
            'Meta': {'object_name': 'SiteSetting'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        u'contentimport.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        u'contentimport.teachergroup': {
            'Meta': {'object_name': 'TeacherGroup'},
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contentimport.ContentItem']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'contentimport.teachergroupmembership': {
            'Meta': {'unique_together': "(('item', 'group'),)", 'object_name': 'TeacherGroupMembership'},
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'featured_end': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'featured_start': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contentimport.TeacherGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contentimport.ContentItem']"})
        }
    }

    complete_apps = ['contentimport']