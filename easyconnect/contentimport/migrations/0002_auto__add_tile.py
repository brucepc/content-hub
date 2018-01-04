# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tile'
        db.create_table(u'contentimport_tile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            #('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('url_string', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('url_target', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('display_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('read_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('teacher_tile', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            
            ('icon', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('storage_folder', self.gf('django.db.models.fields.CharField')(max_length=300)),
            
        ))
        db.send_create_signal(u'contentimport', ['Tile'])


    def backwards(self, orm):
        # Deleting model 'Tile'
        db.delete_table(u'contentimport_tile')


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
        },
        u'contentimport.tile': {
            'Meta': {'object_name': 'Tile'},
            'display_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            #'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url_string': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'url_target': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'teacher_tile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'storage_folder': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
        }
    }

    complete_apps = ['contentimport']