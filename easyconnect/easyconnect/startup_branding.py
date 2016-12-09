#parse additional branding xml and generate associated css
from bs4 import BeautifulSoup
import shutil
import os
from django.conf import settings
EC_ROOT = getattr(settings, 'EC_ROOT', None)

def get_branding():

    if os.path.isdir('/srv/easyconnect'): # On device
        target_css = '/srv/static/stylesheets/branding.css'
        manifest_base = os.path.join('/customize_brand')
        brand_images_target = '/srv/static/images/custom_brand_images'
    else:
        target_css = os.path.join(EC_ROOT, 'static_source', 'stylesheets', 'branding.css')
        manifest_base = os.path.join(EC_ROOT, 'customize_brand')
        brand_images_target = os.path.join(EC_ROOT, 'static_source', 'images', 'custom_brand_images')

    manifest_xml = os.path.join(manifest_base, 'customize_brand.xml')
    if not os.path.isfile(manifest_xml):
        manifest_xml = os.path.join(EC_ROOT, 'customize_brand', 'default_brand.xml')
        manifest_base = os.path.join(EC_ROOT, 'customize_brand')

    f = open(manifest_xml)
    soup = BeautifulSoup(f, 'xml')
    brand_elements = {
        'company-logo': '',
	    'content-hub-logo': '',
	    'brand-logo': '', 
	    'lesson-planner-logo': '',
	    'banner-bkgnd-color': '',
	    'buttons-icons-color': '', 
	    'buttons-icons-highlighted-color': ''
    }

    these_are_images_because_we_cant_have_propper_attributes = {
        'company-logo',
	    'content-hub-logo',
	    'brand-logo', 
	    'lesson-planner-logo'
    }
    #changing to a fixed image name so they can be referenced in the html source without injection
    dest_rename = {
        'company-logo':         'brand-edu-logo.png',
	    'content-hub-logo':     'content-hub-text.png',
        'brand-logo':           'class-connect-text.png',
	    'lesson-planner-logo':  'lesson-planner-text.png'
    }

    #prep target folder
    if os.path.isdir(brand_images_target):
        for filename in os.listdir(brand_images_target):
            os.remove(os.path.join(brand_images_target, filename))

    for brand_element in brand_elements:
        brand_val = soup.find(brand_element)
        if brand_val:
            brand_elements[brand_element] = brand_val.string
            if brand_element in these_are_images_because_we_cant_have_propper_attributes:
                copy_brand_images(brand_val.string, dest_rename[brand_element], manifest_base, brand_images_target)

    # since we have no control over the inconsistently named keys
    # do one more pass and replace keys with underscores to use as variables
    new_dict = {}
    for brand_element in brand_elements:
        new_dict[brand_element.replace('-', '_')] = brand_elements[brand_element]

    try:
        render_to_file('branding.css', target_css, new_dict)
    except:
        pass


    return brand_elements

from django.template.loader import render_to_string
def render_to_file(template, filename, context):
    open(filename, "w").write(render_to_string(template, context))

def copy_brand_images(source_imagename, dest_imagename, source, destination):
    fullsource = os.path.join(source, source_imagename)

    try:
        a = os.path.isfile(fullsource)
        shutil.copy(fullsource, os.path.join(destination, dest_imagename))
    except Exception as e:
        pass