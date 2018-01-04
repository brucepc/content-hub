from __future__ import division # needed for proper division in generate_tag_scores 
from __future__ import absolute_import # needed by celery for async tasks

#import datetime
import hashlib
import logging
import mimetypes
import os
import shutil
import threading
import time
import zipfile
import subprocess
import re

from threading import Thread

from shutil import rmtree, copytree

from django.conf import settings
from django.core import management
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Max, Min
from django.db.models.signals import pre_delete, post_delete, post_save, m2m_changed
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from contentimport.lib import u_slugify
from contentimport.lib import isThereEnoughSpace
from contentimport.lib import getSaveLocation
from contentimport.lib import getMediaURL
from bs4 import BeautifulSoup

import requests
from time import sleep

from contentimport.lib import generate_tag_scores
from contentimport.manifestparser import ManifestParser
from contentimport.models import ContentItem, Category, Package, PackageMembership, Tag, Category, RemoteAPI

from django.utils.translation import ugettext as _

MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', None)
MEDIA_URL = getattr(settings, 'MEDIA_URL', None)
PRELOAD_CONTENT_DIR = getattr(settings, 'PRELOAD_CONTENT_DIR', None)
MICROSITE_DIR = getattr(settings, 'MICROSITE_DIR', None)

REMOTE_CONTENT_DIR = getattr(settings, 'REMOTE_CONTENT_DIR', None)
UPLOAD_CONTENT_DIR = getattr(settings, 'UPLOAD_CONTENT_DIR', None)
ANCHOR_FILE_NAME = getattr(settings, 'ANCHOR_FILE_NAME', '_ec.anchor')

logger = logging.getLogger(__name__)

from celery.contrib.methods import task_method

class Importer:
    """
    optionally takes a path, checks to see what it is and passes it on
    """
    item_ids_added = []
    isAsync = False
    preloaded = False
    asyncProcessID = ''
    usbError = None
    empty_package = None
    MPT_fail = True
    micrositeURL = ''
    storageLocation = ''
    #storageBuffer = getattr(settings, 'STORAGE_BUFFER_SIZE_BYTES', None)
    outOfSpaceError = None    

    def __init__(self, contentpath=None, metadata={}, copy_to_preload=False, copy_to_upload=False, is_preloaded=False, zip_unpack=True, asynchronous=False, isMPT=False, isMicrosite=False):
        self.isAsync = asynchronous
        self.preloaded = is_preloaded
        is_ims = False
        if contentpath:
            validate = URLValidator()
            try:
                validate(contentpath)
            except:
                if copy_to_preload or copy_to_upload:
                    contentpath = self.copy_to_media(contentpath, copy_to_preload, copy_to_upload, isMicrosite)
                #if os.path.isdir(contentpath):
                    #self.directory(contentpath)
                #elif os.path.isfile(contentpath):
                
                #test usb removal
                #contentpath= None
                #self.usbError = True

                if contentpath: # will be none, if copy from usb failed
                    if os.path.isfile(contentpath):
                        if contentpath.lower().endswith('.zip') and zipfile.is_zipfile(contentpath) and self.is_zipfile_valid(contentpath, isMPT):
                            if isMicrosite:
                                self.unzip_microsite(contentpath)
                            else:
                                self.MPT_fail = False
                                if self.isAsync:
                                    job = self.zip_handler.delay(contentpath, metadata=metadata, is_preloaded=is_preloaded, zip_unpack=zip_unpack, objectinstance=self)
                                    self.asyncProcessID = job.id
                                else:
                                    #also microsite route
                                    is_ims = self.zip_handler(contentpath, metadata=metadata, is_preloaded=is_preloaded, zip_unpack=zip_unpack, objectinstance=self)
                        else:
                            if not self.isAsync:
                                self.singlefile(contentpath, metadata, is_preloaded)

                            if contentpath.lower().endswith('.zip') and not zipfile.is_zipfile(contentpath):
                                #already check this, now cleanup if invalid
                                
                                if contentpath:
                                    try:
                                        os.remove(contentpath)
                                    except:
                                        pass
                    else:
                        logger.warn("Tried and failed to use Importer with contentpath(1): " + str(contentpath))
                else:
                    logger.warn("Failed to import contentpath(1): " + str(contentpath))
            else:
                self.remotefile(contentpath, metadata)

            logger.info("Updating tag scores")
            generate_tag_scores()
        else:
            logger.warn("Tried and failed to use Importer with contentpath(2): " + str(contentpath) + ". Maybe you're not actually importing a file though...")

    def is_zipfile_valid(self, path, isMPT):
        if isMPT:
            #do validity check
            '''
            cmd = ['7z', 't', path]
            sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            result = sp.communicate()[0]
            '''
            return True
        else:
            return True

    def p7zExtract(self, filename, output, secs):
        '''
	    file', help='file to extract'
	    path', help='output path for extracted'
	    time', help='time (in secs) to report back'
	    '''
        logfile = filename + "_log.txt"
        total = self.getTotalFiles(filename)

        t = Thread(target=self.extractFiles, args=(filename, output, logfile, ))
        t.start()

        while t.is_alive():

            if not os.path.isfile(logfile):
                continue

            count = self.getExtractCount(logfile)
            if int(count) > int(total):
                count = total
            self.zip_handler.update_state(state='UNZIPPING', meta={ 'unzip_percent': str(count) + " / " + total })
            time.sleep(secs)

        count = self.getExtractCount(logfile)
        os.remove(logfile);
        return True
        
    def getTotalFiles(self, filename):
        try:
            cmd = ['7z', 'l', filename]
            self.executeCmd(cmd, 'list.txt')
            regx = re.compile(r'([0-9]+) files')
            match = regx.search(open('list.txt').read())
            os.remove('list.txt')
            return str(match.group(1))
        except:
            pass
        return '~'

    def extractFiles(self, filename, dest, outfile):
        cmd = ['7z', 'x', filename, '-o' + dest]
        self.executeCmd(cmd, outfile)

    def executeCmd(self, cmd, outfile):
        with open(outfile, 'w') as outputfile:
            sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=outputfile)
            result = sp.communicate()[0]

    def getExtractCount(self, filename):
        try:
            txt = open(filename).read()
            regx = re.compile(r'Extracting +')
            count = len(regx.findall(txt))
        except:
            logger.warn('~~~~~~~~~~~~~~~ Error with 7zip logfile: ' + filename)
            return '~'
        return count
       
    def extract_zip(self, zipfilepath, destfilepath):
        secs = 0.1
        #if self.isAsync:
        #    self.zip_handler.update_state(state='UNZIPPING', meta={ 'unzip_percent': 'preparing...' })
        
        if os.path.isdir("/srv/easyconnect") or True:
            if self.isAsync:
                self.p7zExtract(zipfilepath, destfilepath, secs)
            else:
                cmd = ['7z', 'x', zipfilepath, '-o' + destfilepath]
                sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                result = sp.communicate()[0]
            
        else:
            fh = open(zipfilepath, 'rb')
            z = zipfile.ZipFile(fh)
            z.extractall(destfilepath.encode('utf8'))
            fh.close()

        #if self.isAsync:
        #    self.zip_handler.update_state(state='UNZIPPING', meta={ 'unzip_percent': 'Complete' })

    def delete_package(self, id):
        if id:
            zippath = ''
            try:
                AssocItems = []
                exists = Package.objects.get(pk=id)
                if exists:
                    zippath = exists.package_file
                    associated_ids = Package.objects.filter(package_file=zippath).values_list('id', flat=True)
                    AssocItems = ContentItem.objects.filter(packagemembership__package_id__in=associated_ids)

                for contentItem in AssocItems:
                    contentItem.delete()

                exists = Package.objects.filter(package_file=zippath)
                if exists:
                    for ex in exists:
                        ex.delete()
            except Package.DoesNotExist:
                pass

            if zippath:
                try:
                    os.remove(zippath)
                except:
                    pass

                original_zip = zippath.replace('content_dir/', '')
                try:
                    os.remove(original_zip)
                except:
                    pass
    
    def copy_to_media(self, contentpath, preloaded, uploaded, isMicrosite):
        """
        copy the contentpath to the file upload directory, for example if the contentpath points 
        to a USB directory that might not be there in the future
        """
        if isMicrosite:
            mediadir = MEDIA_ROOT + MICROSITE_DIR
        else:        
            mediadir = MEDIA_ROOT + (UPLOAD_CONTENT_DIR if uploaded else PRELOAD_CONTENT_DIR)
                

        #logger.info("Copying " + contentpath + " to " + mediadir)

        # not called from inside a task
        #if self.isAsync:
        #    self.zip_handler.update_state(state='COPYING', meta={ 'copy_percent': '' })

        #fs = FileSystemStorage(location=mediadir)
        if os.path.isdir(contentpath):
            logger.info("Attempt to copy a directory:" + contentpath)
            # AIDAN comented this out as Dave said it is no longer used
            #head, tail = os.path.split(contentpath[:-1])
            #saved_name = slugify(tail)
            #if uploaded:
            #    saved_name = fs.get_available_name(saved_name)
            #else:
            #    if fs.exists(saved_name):
            #        try:
            #            fs.delete(saved_name)
            #            os.remove(mediadir + saved_name)
            #        except:
            #            pass
            #copytree(contentpath, mediadir + saved_name)

        elif os.path.isfile(contentpath):
            
            filesize = self.get_file_size(contentpath)
            if isMicrosite:
                filesize = filesize * 3 #multiple filesize by 3 if it will be extracted
            mediadir = getSaveLocation(filesize, mediadir)
            fs = FileSystemStorage(location=mediadir)
            if isThereEnoughSpace(filesize, mediadir):
                head, tail = os.path.split(contentpath)
                if uploaded:
                    with open(contentpath, 'rb') as file_obj:
                        saved_name = fs.save(tail, file_obj)
                else:
                    if fs.exists(tail):
                        try:
                            fs.delete(tail)
                            os.remove(mediadir + tail)
                        except:
                            pass
                    head, tail = os.path.split(contentpath)
                    try:
                        with open(contentpath, 'rb') as file_obj:
                            saved_name = fs.save(tail, file_obj)
                    except:
                        self.usbError = True
                        return None
            else:
                self.outOfSpaceError = True;
                return None
                        # not called from inside a task
        #if self.isAsync:
        #    self.zip_handler.update_state(state='COPYING', meta={ 'copy_percent': 'Complete' })

        return mediadir + saved_name


    from django.shortcuts import render_to_response
    from django.template import RequestContext
    from django.http import HttpResponse
    import json
    from django.views.decorators.csrf import csrf_exempt
    from celery.result import AsyncResult

    # async celery task definitions
    # asynchronos scheduled tasks using celery
    # for package management user feedback
    from easyconnect.celery import app
    
 
    @app.task(bind=True)
    def zip_handler(self, zipfilepath, metadata={}, is_preloaded=False, zip_unpack=True, filter='task_method', objectinstance=None):
        """
        decide if this is a package or not and pass along appropriately
        """
        if objectinstance.isAsync:
            self.update_state(task_id=self.request.id, state='UNZIPPING', meta={ 'unzip_percent': '' })

        is_ims = False
        try:
            with zipfile.ZipFile(zipfilepath, 'r') as package:
                file_list = package.namelist()
                # check for required files
                #if all(x in file_list for x in ['imsmanifest.xml', 'imscp_v1p1.xsd']):
                '''
                if all(x in file_list for x in ['imsmanifest.xml']):
                    logger.info("Package file found")
                    self.package(zipfilepath)
                '''

                has_manifest = False
                manifest_name = 'imsmanifest.xml'
                for x in file_list:
                    if x.startswith('imsmanifest'):
                        has_manifest = True
                        manifest_name = x
            
                if has_manifest:
                    logger.info("Package file found")
                    is_ims = True
                    objectinstance.package(zipfilepath, manifest_name, is_preloaded)
                #elif not any(x in file_list for x in ['imsmanifest.xml', 'imscp_v1p1.xsd']):
                else:
                    logger.info("Zip file found")
                    if zip_unpack:
                        objectinstance.notpackage_zip(zipfilepath, metadata=metadata, is_preloaded=is_preloaded, zip_unpack=zip_unpack)
                    else:
                        objectinstance.singlefile(zipfilepath, metadata=metadata, is_preloaded=is_preloaded)
                '''
                else:
                    logger.warn("Package found but missing required file(s). Ignoring.")
                '''
        except Exception as e:
            return 'FAILURE'
        if objectinstance.empty_package:
            return 'FAILURE'
        return is_ims

    #daveh - tags and categories not in expected format
    def singlefile(self, contentpath, metadata={}, is_preloaded=False):
        """
        takes a path, and optionally metadata, gets details of a file and creates a ContentItem for it in the database (and categories if needed)
        """
        logger.info("Importer found: File!")
        logger.info("singlefile contentpath: " + contentpath)


        file_path, file_name = os.path.split(contentpath)
        file_title, file_extension = os.path.splitext(file_name)

        categories = metadata.get('categories', None)
        tags = metadata.get('tags', None)
        mime_type = metadata.get('mime_type', None)

        new_item = self.create_contentitem_object(contentpath, metadata)
        new_item.save() # have to save the instance before we can add other instances (tags, categories) to it

        cat_to_ci_map = []
        if categories is not None:
            if 'ids' in categories:
                if 'list' in categories:
                    list_to_pass = categories['list']
                else:
                    list_to_pass = categories['ids']
                cat_to_ci_map.append([ new_item.id, list_to_pass])
                #self.create_categories(categories)
                self.create_category_relationships(cat_to_ci_map, id_list=True)

        tag_to_ci_map = []
        if tags:
            if 'list' in tags:
                list_to_pass = tags['list']
                list_to_pass = filter(None, list_to_pass) #remove empty
            else:
                if 'ids' in tags:
                    list_to_pass = tags['ids']
                else:
                    list_to_pass = []
            
            if list_to_pass and list_to_pass.count is not None: #prevent if empty
                tag_to_ci_map.append([ new_item.id, list_to_pass ])
                '''
                if not tags['ids']:
                    self.create_tags(tags['list'])
                '''
                self.create_tag_relationships(tag_to_ci_map, id_list=list_to_pass)

        new_item.save() # save again cause it's quicker to trigger a search index update this way (to catch categories and tags added)

        self.item_ids_added.append(new_item.id)
        logger.info("singlefile import complete")
        return new_item

    def create_contentitem_object(self, contentpath, metadata={}):

        title = metadata.get('title', None)
        file_size = metadata.get('file_size', None)
        description = metadata.get('description', None)
        categories = metadata.get('categories', None)
        tags = metadata.get('tags', None)
        mime_type = metadata.get('mime_type', None)
        identifier = metadata.get('identifier', None)

        file_path, file_name = os.path.split(contentpath)
        file_title, file_extension = os.path.splitext(file_name)

        if mime_type is None:
            mime_type, mime_encoding = mimetypes.guess_type(contentpath) # returns None if it can't figure it out

        if mime_type == 'text/html':
            with open(contentpath, 'r') as f:
                data_html = f.read()
            soup = BeautifulSoup(data_html)
            if not title or title.isspace():
                try:
                    title = soup.find('title').next
                except:
                    title = None
            if not description or description.isspace():
                try:
                    description = soup.find('meta', {'name':'description'})['content']
                except:
                    description = None

        if not title or title.isspace():
            title = file_title
        if file_size is None:
            from urlparse import urlparse
            file_only_path = urlparse(contentpath).path
            to_parse = contentpath
            if file_only_path:
                to_parse = file_only_path
            try:
                file_size = os.path.getsize(to_parse)
            except:
                file_size = 0
        # path needs to be relative to MEDIA_ROOT
        if(MEDIA_ROOT.lower().startswith('c:')):
            # fix for issue in windows debug environment where c: is sometimes uppercase
            if file_path.lower().startswith(MEDIA_ROOT.lower()):
                content_file = file_path.replace(MEDIA_ROOT.lower(), MEDIA_URL)
                content_file = content_file + '/' + file_name
            else:
                content_file = MEDIA_URL + file_path + '/' + file_name
        else:
            # retaining this method for legitimate cases where paths differ by case only
            if file_path.startswith(MEDIA_ROOT):
                content_file = file_path.replace(MEDIA_ROOT, MEDIA_URL)
                content_file = content_file + '/' + file_name
            else:
                content_file = MEDIA_URL + file_path + '/' + file_name

        is_uploaded = False
        #if content_file.startswith( UPLOAD_CONTENT_DIR ):
        if UPLOAD_CONTENT_DIR in content_file:
            is_uploaded = True
            
        file_hash = self.md5_hash_file(contentpath)
        new_item = ContentItem(content_file=content_file, title=title, file_size=file_size, mime_type=mime_type, description=description, file_hash=file_hash, identifier=identifier, uploaded=is_uploaded)

        return new_item

    def create_tags(self, tags):
        """
        accept a list of tags and create them if they don't already exist
        """
        logger.info("Creating tags")
        #if self.isAsync:
        #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Creating tags...' })
        with transaction.commit_on_success():
            tag_obj_list = []
            tag_update_list = [] #for existing, set locked if preloaded
            all_tags = Tag.objects.all()
            for tag in tags:
                
                tag_clean = u_slugify(tag)
                
                if tag_clean: #i.e. not empty string
                    if not all_tags.filter(text=tag_clean).exists():
                        tag_obj_list.append( Tag(text=tag_clean, locked=self.preloaded) )
                    else:
                        Tag.objects.filter(text=tag_clean).update(locked=True)
            try:
                if tag_obj_list:
                    Tag.objects.bulk_create(tag_obj_list)
            except:
                logger.info("Error during tag bulk create")
            else:
                logger.info("Complete")

    def create_categories(self, categories):
        """
        accept a list of lists each representing a category hierarchy (broad to narrow) and create those categories in the database
        """
        logger.info("Creating categories")
        #if self.isAsync:
        #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Creating categories...' })
        if categories is not None:
            for category_hierarchy in categories:
                x = 0
                parent_tmp = None
                while x < len(category_hierarchy):
                    try:
                        parent_tmp, cat_created = Category.objects.get_or_create(name=category_hierarchy[x], parent=parent_tmp)
                    except:
                        logger.info("Error during category (" + category_hierarchy[x] + ") create")

                    x += 1

    def create_tag_relationships(self, tag_to_ci_map, id_list=False):
        """
        accept a list of content item to tag mappings like: [ [ ci_id, [ tag, ... ] ], ... ] and bulk_create the relationships
        id_list being true means we'll get a tag list of ids instead of names
        """
        TagThroughModel = ContentItem.tags.through

        all_tags_lookup = {}
        tags_to_add = []
        tag_pairs_added = []

        if not id_list:
            for tag in Tag.objects.values('id', 'text'):
                all_tags_lookup[tag['text']] = tag['id']

        # create tag memberships
        for pairings in tag_to_ci_map:
            ci_id = pairings[0]
            tags = pairings[1]

            if tags is not None:
                for tag in tags:
                    if id_list:
                        tag_id = tag
                    else:
                        tag_id = all_tags_lookup.get(u_slugify(tag), None)
                    id_pair = (ci_id, tag_id)
                    if id_pair not in tag_pairs_added and tag_id is not None: # Avoid triggering a duplication IntegrityError #And Null id integrity error
                        ttm = TagThroughModel(contentitem_id=ci_id, tag_id=tag_id)
                        tags_to_add.append(ttm)
                        tag_pairs_added.append(id_pair)

        logger.info("Adding tag relationships to database")
        try:
            TagThroughModel.objects.bulk_create(tags_to_add)
        except Exception as e:
            logger.info("Error during tag relationship bulk create")
            logger.exception(e)
        else:
            logger.info("Complete")

    def create_category_relationships(self, cat_to_ci_map, id_list=False):
        CategoryThroughModel = ContentItem.categories.through

        cats_to_add = []
        cat_pairs_added = []

        for pairings in cat_to_ci_map:
            ci_id = pairings[0]
            categories = pairings[1]

            if categories is not None:
                if not any(x is None for x in categories):
                    if id_list:
                        for category in categories:
                            id_pair = (ci_id, category)
                            if id_pair not in cat_pairs_added:
                                ctm = CategoryThroughModel(contentitem_id=ci_id, category_id=category)
                                cats_to_add.append(ctm)
                                cat_pairs_added.append(id_pair)
                    else:
                        cat_tmp = None
                        x = 0
                        while x < len(categories):
                            cat_tmp = Category.objects.get(name=categories[x], parent=cat_tmp)
                            x += 1
                        cat_id = cat_tmp.pk
                        id_pair = (ci_id, cat_id)
                        if id_pair not in cat_pairs_added:
                            ctm = CategoryThroughModel(contentitem_id=ci_id, category_id=cat_id)
                            cats_to_add.append(ctm)
                            cat_pairs_added.append(id_pair)

        if cats_to_add.count is not None:
            logger.info("Adding category relationships to database")
            try:
                CategoryThroughModel.objects.bulk_create(cats_to_add)
            except Exception as e:
                logger.info("Error during category relationship bulk create")
                logger.exception(e)
            else:
                logger.info("Complete")

    def remotefile(self, contentpath, metadata={}):
        """
        handles files that are on the end of URLs, not on disk
        """
        logger.info("Importer found: URL!")
        logger.info("remotefile contentpath: " + contentpath)
        path, filename = os.path.split(contentpath)
        r = requests.get(contentpath, stream=True)
        
        api_source = metadata.get('api_source', '')
        saved_path = MEDIA_ROOT + REMOTE_CONTENT_DIR + api_source + filename

        if r.status_code == 200:
            with open(saved_path, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)

        if os.path.isfile(saved_path):
            self.singlefile(saved_path, metadata)
    
    def package(self, zipfilepath, manifest_name, is_preloaded=False):
        """
        handles a proper zipped package
        """
        logger.info("Importer found: Package!")
        logger.info("package zipfilepath: " + zipfilepath)
        filepath, filename = os.path.split(zipfilepath)
        packagefile = filepath + '/' + os.path.splitext(filename)[0]

        item_name, file_extension = os.path.splitext(filename)
        replacement = False

        with zipfile.ZipFile(zipfilepath, 'r') as package:
            extract_dir = filepath + '/' + item_name + '/'
            # uploading a replacement package implies the old one is to be deleted
            if os.path.exists(extract_dir):
                logger.warn(extract_dir + " already exists. Replacing existing package.")
                # either it's a duplicate or just a similarly named one
                # TODO: either way, the user should be warned in the UI that uploading this will replace the old and be given a chance to back out
                replacement = True

            # if the item_name is the same as an existing, we need to worry about replacement
            if replacement:
                try:
                    Package.objects.filter(package_file=packagefile).delete()
                    #return # uncomment this to allow deletion, but stop new content being written
                except OSError as e:
                    logger.error("Could not delete existing package dir: " + extract_dir)
                    logger.info("Deleting uploaded file")
                    self.del_file(filepath, filename)
                    return

            logger.info('Unzipping package to: ' + extract_dir)
            
            #Aidan added 7zip unzip to handle non-ascii chars
            self.extract_zip(zipfilepath, extract_dir)
            if self.isAsync:
                self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Adding to database' })
            #package.extractall(extract_dir)
            logger.info('Unzip complete')
            #if self.check_files(manifest, extract_dir):
            logger.info("Parsing manifest")
            parser = ManifestParser()

            #manifest_doc = package.read('imsmanifest.xml')
            manifest_doc = package.read(manifest_name)
            

            package_data = parser.parse_manifests(manifest_doc)

            if package_data is None:
                logger.warn("No entries found in manifest!")
            
            # tags
            if package_data['tags'] is not None:
                self.create_tags(package_data['tags'])

            # categories
            if package_data['categories'] is not None:
                self.create_categories(package_data['categories'])

            #if self.isAsync:
            #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Beginning Import...' })
            #with transaction.commit_on_success():
            if True:
                ci_obj_list = []
                pk_obj_list = []
                logger.info("Creating packages and contentitems...")
                for manifest in package_data['manifests']:
                    pak = manifest['package']
                    #pak_title = pak.get('title', None)
                    pak_title = filename
                    pak_description = pak.get('description', None)
                    pak_id = pak.get('identifier', None)
                    pak_version = pak.get('version', None)
                    pak_hash = self.md5_hash_file(zipfilepath)
                    pak_size = self.get_file_size(zipfilepath)
                    pak_obj = Package(title=pak_title, description=pak_description, package_file=packagefile, identifier=pak_id, version=pak_version, file_hash=pak_hash, preloaded=is_preloaded, filesize=pak_size)
                    pk_obj_list.append(pak_obj)

                    add_to_pk = []

                    for resource in manifest['resources']:
                        file_path = extract_dir + resource['path']
                        ci_obj = self.create_contentitem_object(file_path, resource)
                        ci_obj_list.append(ci_obj)
                        add_to_pk.append([ci_obj, resource])

                logger.info("Complete")
                #if self.isAsync:
                #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Adding packages to database...' })

                logger.info("Adding packages to database...")
                try:
                    Package.objects.bulk_create(pk_obj_list)
                except:
                    logger.error("Error adding packages to database")
                    logger.exception()
                else:
                    logger.info("Complete")

                logger.info("Adding content items to database...")
                try:
                    ContentItem.objects.bulk_create(ci_obj_list)
                except:
                    logger.error("Error adding packages to database")
                    logger.exception()
                else:
                    logger.info("Complete")

                # Now to run through everything again
                # It's faster to do it this way, trust me
                mem_obj_list = []
                tag_to_ci_map = []
                cat_to_ci_map = []

                logger.info("Parsing package, category, and tag relationships...")
                # Iterate through the package_data again
                for manifest in package_data['manifests']:
                    #if self.isAsync:
                    #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Found Manifest...' })
                    logger.info("Found package")
                    pack = manifest['package']
                    pack_id = pack.get('identifier', None)
                    try:
                        pack_obj = Package.objects.get(identifier=pack_id, package_file=packagefile)
                    except MultipleObjectsReturned as e:
                        logger.error('Multiple objects returned for identifier: ' + str(pack_id) + '. There should just be one!')
                    except:
                        logger.error('Could not retrieve package object based on identifier: ' + str(pack_id))
                        logger.exception()
                        self.del_file(filepath, filename)

                    #logger.info(pack_obj)

                    for resource in manifest['resources']:
                        #if self.isAsync:
                        #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Creating resources...' })
                        logger.info("Found resource. Identifier: " + resource['identifier'])
                        # get previously created ContentItem
                        res_obj = None
                        try:
                            if (MEDIA_ROOT.lower().startswith('c:')):
                                content_file = extract_dir.replace(MEDIA_ROOT.lower(), '')
                            else:
                                content_file = extract_dir.replace(MEDIA_ROOT, '')
                            check_file = MEDIA_URL + content_file

                            res_obj = ContentItem.objects.get(identifier=resource['identifier'], content_file__startswith=check_file) # Identifiers are required to be unique, but who knows what other packages are using
                            
                        except MultipleObjectsReturned as e:
                            logger.error('Multiple objects returned for identifier: ' + str(resource['identifier'])) + '. There should just be one!'
                        except:
                            logger.error('No contentitem found for this resource in database!')

                        # create package membership
                        
                        mem_obj = PackageMembership(package=pack_obj, resource=res_obj, position=resource['position'])
                        mem_obj_list.append(mem_obj)
                        ci_id = res_obj.pk
                        # map tag memberships
                        tags_dict = resource['tags']
                        if tags_dict is not None:
                            tags = tags_dict['list']
                            tag_to_ci_map.append([ ci_id, tags ])
                        # map category memberships
                        categories_dict = resource['categories']
                        if categories_dict is not None:
                            categories = categories_dict['list']
                            cat_to_ci_map.append([ ci_id, categories ])
                        

                logger.info("Complete")

                logger.info("Adding package membership relationships to database...")
                try:
                    PackageMembership.objects.bulk_create(mem_obj_list)
                except:
                    logger.info("Error during package membership bulk create")
                else:
                    logger.info("Complete")

                if tag_to_ci_map:
                    self.create_tag_relationships(tag_to_ci_map)

                if cat_to_ci_map:
                    self.create_category_relationships(cat_to_ci_map)

        #if self.isAsync:
        #    self.zip_handler.update_state(task_id=self.zip_handler.request.id, state='IMPORTING', meta={ 'import_percent': 'Finishing...' })
        #logger.info("Updating log")
        # TODO: new log entry added x items from package file y

        # Uploaded file gets deleted no matter what
        logger.info("Deleting uploaded file")
        #self.del_file(filepath, filename)
        logger.info("Package done")


    def unzip_microsite(self, zipfilepath):
        """
        handles zips that are microsites, extract and dont import as content items, return a URL
        """
        filepath, filename = os.path.split(zipfilepath)
        zipname, extension = os.path.splitext(filename)
        saved_dir = filepath
        fs = FileSystemStorage(location=saved_dir)
        if zipname:
            if fs.exists(zipname):
                zipname = fs.get_available_name(zipname)
            saved_dir = saved_dir + '/' + zipname
            os.makedirs(saved_dir)

        self.extract_zip(zipfilepath, saved_dir)

        #need to save both as if user overrides that we return to something in a lower directory we still need to track the root location
        self.storageLocation = getMediaURL(saved_dir) #saved_dir.replace(MEDIA_ROOT, MEDIA_URL)
        self.micrositeURL = self.storageLocation#saved_dir.replace(MEDIA_ROOT, MEDIA_URL)

        for fname in os.listdir(saved_dir):
            if fname.lower() == 'index.html' or fname.lower() == 'index.htm':
                self.micrositeURL = os.path.join(getMediaURL(saved_dir), fname)

        #Delete the zip
        try:
            os.remove(zipfilepath)
        except:
            logger.warn("Attempted file deletion failed for file: " + zipfilepath)
        else:
            logger.warn("Deleted file: " + zipfilepath)

        

    def notpackage_zip(self, zipfilepath, metadata={}, is_preloaded=False, zip_unpack=True):
        """
        handles zips that aren't packages or aren't trying to be
        """

        #ignore title for this type of zip
        if metadata:
            if 'title' in metadata:
                metadata.pop('title', None)

        logger.info("Importer found: A zip that's not a package!")
        logger.info("notpackage_zip zipfilepath: " + zipfilepath)
        # extract (into root dir, not it's own dir)
        filepath, filename = os.path.split(zipfilepath)
        zipname, extension = os.path.splitext(filename)

        saved_dir = filepath
        fs = FileSystemStorage(location=saved_dir)
        if zipname:
            if fs.exists(zipname):
                zipname = fs.get_available_name(zipname)
            saved_dir = saved_dir + '/' + zipname
            os.makedirs(saved_dir)
        
        #import subprocess
        #cmd = ['7z', 'x', zipfilepath, '-o' + saved_dir]
        #sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        self.extract_zip(zipfilepath, saved_dir)

        if self.isAsync:
            self.zip_handler.update_state(state='IMPORTING', meta={ 'import_percent': 'Adding to database' })
        c_obj_list = []
        filenames = next(os.walk(saved_dir))[2]

        #if nothing at root set error
        if not filenames:
            self.empty_package = True
            try:
                rmtree(saved_dir)
            except:
                pass
            try:
                os.remove(zipfilepath)
            except:
                pass
            if self.isAsync:
                return

        totalFils = str(len(filenames))
        #for fname in filenames:
        for curFil, fname in enumerate(filenames):
            uni_filename = unicode(fname)
            saved_path = saved_dir + '/' + uni_filename
            
            # Build list of items to Import
            c_obj_list.append(self.singlefile(saved_path, metadata=metadata))
            #if self.isAsync:
            #    self.zip_handler.update_state(state='IMPORTING', meta={ 'import_percent': 'copying ' + str(curFil) + ' of ' + totalFils })
          
                            
        #create a package and add items to it
        import uuid
        if c_obj_list:
            guid = str(uuid.uuid4())
            pak_obj = Package(title=filename,
                            description='description',
                            package_file=saved_dir, # should be the folder unzipped to
                            identifier=guid,
                            version='1',
                            file_hash='hash',
                            preloaded=is_preloaded,
                            filesize=self.get_file_size(zipfilepath))
            pak_obj.save()
            pack_position = 0

            totalObjs = str(len(c_obj_list))

            for curObj, res_obj in enumerate(c_obj_list):
                #if self.isAsync:
                #    self.zip_handler.update_state(state='IMPORTING', meta={ 'import_percent': 'parsing ' + str(curObj) + ' of ' + totalObjs })
                mem_obj = PackageMembership(package=pak_obj, resource=res_obj, position=pack_position)
                mem_obj.save()
                pack_position += 1

        # Delete the zip
        '''
        try:
            os.remove(zipfilepath)
        except:
            logger.warn("Attempted file deletion failed for file: " + zipfilepath)
        else:
            logger.warn("Deleted file: " + zipfilepath)
        '''

    def del_file(self, filedir, filename):
        """
        attempt to delete file filename from directory filedir, return true or false on success or failure
        """
        try:
            os.remove(filedir + '/' + filename)               
            #fs = FileSystemStorage(location=filedir)
            #if fs.exists(filename):
            #    fs.delete(filename)
        except:
            logger.warn("Attempted file deletion failed for file: " + filedir + '/' + filename)
            return False
        else:
            logger.warn("Deleted file: " + filedir + '/' + filename)
            return True

    def check_files(self, xml, extract_dir):
        """
        makes sure the files references in the manifest actually exist
        """
        fs = FileSystemStorage(location=extract_dir)
        root = xml.getroot()

        for element in root.iter(tag='{*}file'):
            href = element.get('href')
            if not fs.exists(href):
                logger.warn("File referenced in manifest " + href + " doesn't seem to exist")
                return False
        logger.info("File manifest check complete successfully")
        return True

    def gen_file_list(self, directory):
        """
        recursively generates a list of files with full paths
        """
        found_files = []
        fs = FileSystemStorage(location=directory)
        fs_list = fs.listdir(directory)
        for filename in fs_list[1]:
            found_files.append(directory + filename)
        for path in fs_list[0]:
            found_files.append(self.gen_file_list(directory + path + '/'))
        return found_files

    def directory(self, directory):
        """
        adds the directory as a single ContentItem, using a created anchor file as the content_item in the model
        """
        logger.info("Importer found: Directory!")
        logger.info("directory directory: " + directory)

        directory_split = directory.split('/')
        leading, dir_name = os.path.split(directory)
        slugged_dir_name = slugify(dir_name)
        slugged_directory = leading + '/' + slugged_dir_name
        try:
            os.rename(directory, slugged_directory)
        except OSError:
            logger.warn("Unable to slugify directory " + directory + ". Forced to ignore.")
            return
        
        #now = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        anchor_file = slugged_directory + "/" + ANCHOR_FILE_NAME
        try:
            open(anchor_file, 'w').close()
        except OSError:
            logger.warn("Unable to create anchor file " + anchor_file + ". Forced to ignore directory.")
            # Should also delete directory
            return

        logger.info("Importer directory anchor_file created: " + anchor_file)
        self.singlefile(anchor_file, {"title": slugged_dir_name})

    def md5_hash_file(self, filepath):
        if os.path.isfile(filepath):
            md5 = hashlib.md5()
            with open(filepath,'rb') as f:
                for chunk in iter(lambda: f.read(128*md5.block_size), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        else:
            return 'THEREWASAPROBLEMHASHING.com'

    def get_file_size(self, filepath):
        file_size = 0
        if os.path.isfile(filepath):
            try:
                file_size = os.path.getsize(filepath)
            except:
                file_size = 0
        return file_size
