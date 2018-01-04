from __future__ import division # needed for proper division in generate_tag_scores 

#import datetime
import hashlib
import logging
import mimetypes
import os
import shutil
import zipfile
import re

from shutil import rmtree, copytree

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.validators import URLValidator
from django.db.models import Avg, Count, Max, Min
from django.db.models.signals import pre_delete, post_delete, post_save, m2m_changed
from django.dispatch import receiver
from django.template.defaultfilters import slugify

from bs4 import BeautifulSoup as BS


import requests

#from lxml import etree

from contentimport.models import ContentItem, Category, Package, PackageMembership, Tag, Category, RemoteAPI

import time

MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', None)
MEDIA_URL = getattr(settings, 'MEDIA_URL', None)
HDD_DIR = getattr(settings, 'HDD_DIR', None)
REMOTE_CONTENT_DIR = getattr(settings, 'REMOTE_CONTENT_DIR', None)
UPLOAD_CONTENT_DIR = getattr(settings, 'UPLOAD_CONTENT_DIR', None)
ANCHOR_FILE_NAME = getattr(settings, 'ANCHOR_FILE_NAME', '_ec.anchor')
ICONS_DIR = getattr(settings, 'ICONS_DIR', None)

logger = logging.getLogger(__name__)

storageBuffer = getattr(settings, 'STORAGE_BUFFER_SIZE_BYTES', None)

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        logger.info('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res

    return wrapper

def timesince(message, t1):
    t2 = time.time()
    logger.info('%0.3f ms after %s' % ((t2-t1)*1000.0, message))

'''
@receiver(post_delete, sender=ContentItem)
@receiver(m2m_changed, sender=ContentItem.tags.through)
'''


def generate_tag_scores(sender=None, instance=None, **kwargs):
    """
    assign scores to tags from 1 to 7, based on how many contentitems use the tag
    """
    return None
    '''
    tags = Tag.objects.annotate(uses=Count('contentitem'))
    tag_stats = tags.aggregate(Avg('uses'), Min('uses'), Max('uses'))

    for tag in tags:
        #logger.info("tag, uses: " + tag.text + ", " + str(tag.uses))
        #logger.info("tag: avg, min, max: " + str(tag_stats['uses__avg']) + ", " + str(tag_stats['uses__min']) + str(tag_stats['uses__max']))
        if tag.uses > 0:
            max_minus_min = tag_stats['uses__max'] - tag_stats['uses__min']
            max_minus_min = max_minus_min if max_minus_min > 0 else 1

            #logger.info("tag: max_minus_min: " + str(max_minus_min))

            score = ((tag.uses - tag_stats['uses__min']) / max_minus_min) * 7
            score = score if score > 0 else 1
        else:
            score = 0 # tags get deleted when there's no contentitem associated anyway

        #logger.info("tag: score: " + str(score))

        tag.score = int(score)
        tag.save()
    '''
    
@receiver(pre_delete, sender=ContentItem)
def contentitem_pre_cleanup(sender, instance, **kwargs):
    """
    Before we delete the contentitem, we remove the associated soon-to-be-empty tags, categories, packages, etc
    """
    tags = Tag.objects.filter(contentitem__title=instance)

    for tag in tags:
        tag.delete_if_empty_excluding(instance)

    packages = instance.packages.all()

    if not packages:
        return

    associated_ids = packages.values_list('id', flat=True)
    AssocItems = ContentItem.objects.filter(packagemembership__package_id__in=associated_ids)
    if AssocItems.count() <= 1:
        all_packages = Package.objects.filter(package_file=packages[0].package_file)
        all_packages.delete()


# left over from directory import functionality: redundant. 
'''
@receiver(post_delete, sender=ContentItem)
def remove_contentitem_file(sender, instance, **kwargs):
    filepath, filename = os.path.split(instance.content_file.path)
    # Is this contentitem actually a directory?
    if filename == ANCHOR_FILE_NAME:
        # Delete the containing directory and all within it
        rmtree(filepath)
'''

@receiver(post_delete, sender=Package)
def remove_package_directory(sender, instance, **kwargs):
    # Delete the directory (If no other package is using it...)
    if Package.objects.filter(package_file=instance.package_file).count() == 0:
        filepath, filename = os.path.split(instance.package_file)
        dirname, extension = os.path.splitext(filename)
        extract_dir = filepath + '/' + dirname + '/'
        logger.info('No more packages using ' + extract_dir + '. Deleting.')
        try:
            rmtree(extract_dir)
        except OSError as e:
            logger.warn("Couldn't delete " + extract_dir)
            logger.error(e)


@receiver(post_save, sender=RemoteAPI)
def create_api_source_directory(sender, instance, **kwargs):
    # create a dir called instance.title_hash in the remote dir
    try:
        api_dir = MEDIA_ROOT + REMOTE_CONTENT_DIR + instance.title_hash
        os.makedirs(api_dir)
        logger.info("Created the api directory " + api_dir)
    except OSError:
        # Couldn't make the directory!
        instance.delete()
        logger.warn("Couldn't create the api directory for " + api_dir + " so removing api from database")

@receiver(post_delete, sender=RemoteAPI)
def remove_api_source_directory(sender, instance, **kwargs):
    logger.warn("API " + instance.title + " deleted")

import platform
import ctypes
def getAvailableSpace(path):
    "Get the free space (in bytes) of the filesystem containing pathname"
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                return 0

    if not os.path.isdir(directory):
        return 0

    try:
        if platform.system() == 'Windows':
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
                return free_bytes.value
        else:
            logger.info("Getting size of: " + str(path))
            stat = os.statvfs(path)
            # use f_bfree for superuser, or f_bavail if filesystem
            # has reserved space for superuser
            return stat.f_bavail * stat.f_frsize
    except:
        return 0

def isThereEnoughSpace(size, dest):
    "Check if the size required is less than the available space"
    return size < (getAvailableSpace(dest) - storageBuffer)

def getSaveLocation(new_file_size, dest):
    "check if there is enough space on the internal HD if not return path to external if it exists"
    if isThereEnoughSpace(new_file_size, dest) or not os.path.isdir(os.path.join(MEDIA_ROOT, HDD_DIR)) or str(dest).find(os.path.join(MEDIA_ROOT, HDD_DIR)) > -1:
        return dest
    else:
        return str(dest).replace(MEDIA_ROOT, os.path.join(MEDIA_ROOT, HDD_DIR), 1)

def getMediaURL(saveLocation):
    if str(saveLocation).find(MEDIA_ROOT) > -1:
        return str(saveLocation).replace(MEDIA_ROOT, MEDIA_URL)
    else:
        return saveLocation

def get_file_size( filepath):
        file_size = 0
        if os.path.isfile(filepath):
            try:
                file_size = os.path.getsize(filepath)
            except:
                file_size = 0
        return file_size


def upload_handler(request, metadata={}):
    """
    writes file(s) to appropriate spot on disk, collects metadata from the form, calls FileImporter on it
    """
    from datetime import datetime
    timing_now = datetime.now()
    timing_string = timing_now.isoformat(' ')
    new_file = request.FILES['content_file']

    # write the file to disk
    #save_dir = MEDIA_ROOT + UPLOAD_CONTENT_DIR
    # First check if there is enoght space internally and if not return the path the external HD, 
    # the second check below is then a definative check for any free space
    save_dir = getSaveLocation(new_file.size, os.path.join(MEDIA_ROOT, UPLOAD_CONTENT_DIR))

    if isThereEnoughSpace(new_file.size, save_dir):
        fs = FileSystemStorage(location=save_dir)
        if fs.exists(new_file.name):
            new_file.name = fs.get_available_name(new_file.name)
        content_file = fs.save(new_file.name, new_file)
        
        #return MEDIA_URL + UPLOAD_CONTENT_DIR + new_file.name
        return getMediaURL(save_dir) + new_file.name
    else:
        return None

def icon_upload_handler(request, metadata={}):
    """
    writes file(s) to appropriate spot on disk, collects metadata from the form, calls FileImporter on it
    """
    from datetime import datetime
    timing_now = datetime.now()
    timing_string = timing_now.isoformat(' ')
    new_file = request.FILES['icon']

    # write the file to disk
    save_dir = getSaveLocation(new_file.size, os.path.join(MEDIA_ROOT,ICONS_DIR))
    if isThereEnoughSpace(new_file.size, save_dir):
        fs = FileSystemStorage(location=save_dir)
        if fs.exists(new_file.name):
            new_file.name = fs.get_available_name(new_file.name)
        icon = fs.save(new_file.name, new_file)
        #return MEDIA_URL + ICONS_DIR + new_file.name
        return getMediaURL(save_dir) + new_file.name
    else:
        return None

def category_dictionary():
    """
    Returns all categories as a hierarchical dictionary
    """
    cat_dict = []

    categories = Category.objects.all().annotate(uses=Count('contentitem'))
    top_level_categories = Category.objects.filter(parent=None).order_by('name').annotate(uses=Count('contentitem'))

    # Top-leve categories
    for c in top_level_categories:
        c_dict = {
            'pk': c.pk,
            'name': c.name,
            'uses': c.uses,
            'children': [],
        }
        subs = categories.filter(parent=c.pk)

        # Sub categories
        for s in subs:
            subs_dict = {
                'pk': s.pk,
                'name': s.name,
                'uses': s.uses,
                'children': [],
            }
            sub_subs = categories.filter(parent=s.pk)

            # Sub-Sub categories
            for s2 in sub_subs:
                subs2_dict = {
                    'pk': s2.pk,
                    'name': s2.name,
                    'uses': s2.uses,
                }

                subs_dict['children'].append(subs2_dict)

            c_dict['children'].append(subs_dict)

        cat_dict.append(c_dict)

    return cat_dict

#slug for tags (allow non ascii chars)
def u_slugify(str):
    str = str.strip().lower()
    ret = re.sub('@[^\w\-]', '', str.replace(' ', '-'), re.UNICODE)
    ret = ret.replace('--', '-');
    return ret