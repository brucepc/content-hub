# -*- coding: utf-8 -*-
import json
import logging
import base64

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView

from contentimport.importer import Importer

logger = logging.getLogger(__name__)

import os
def list_usb_drives():
    """
    Create list of USB drives attatched to the system with id numbers, names, and paths
    http://udisks.freedesktop.org/docs/1.0.5/ref-dbus.html

    Note: assumes some sort of automounting of drives (apt-get install automount)
    TODO: might want to support exfat, but that's not installed in 12.04 by default
    TODO: should probably set a limit on files or time?
    TODO: more descriptive error if no dbus
    """

    #debug for dev on local device
    dummypath = os.path.dirname(os.path.dirname(__file__)) + '/media/dummy_usb/'
    fake_list = [
        {
            'name': 'Fake USB 1',
            'path': dummypath + 'test_usb_drive_a',
            'id': '0',
        },
        {
            'name': 'Fake USB 2',
            'path': dummypath + 'test_usb_drive_b',
            'id': '1',
        }
    ]

    try:
        import dbus
    except:
        return fake_list # in case of windows, fake it. TODO: remove! (and have better error)

    try:
        bus = dbus.SystemBus() 
    except dbus.DBusException:
        logger.error("DBusException")

    detected_drives = []
    drive_id = 0

    #daveh - the sd card is not dectecable by either interface or media type - therefore the path is used
    sd_card_mount_path = '/media/usbhd-SD'

    ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
    ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')

    #logger.info("**************************************************")
    #logger.info("Enumerating drives")

    for dev in ud_manager.EnumerateDevices():

        device_obj = bus.get_object("org.freedesktop.UDisks", dev)
        device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)

        device_is_drive = device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsDrive")
        device_interface = device_props.Get('org.freedesktop.UDisks.Device', "DriveConnectionInterface")
        device_is_mounted = device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsMounted")
        device_mount_paths = device_props.Get('org.freedesktop.UDisks.Device', "DeviceMountPaths", byte_arrays=True, utf8_strings=True)


        # Check if USB drive OR SD card (based on mount path)
        if (device_interface == 'usb' or (len(device_mount_paths) > 0 and str(device_mount_paths[0]) == sd_card_mount_path)) and device_is_mounted:
            device_is_removable = device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsRemovable")
            device_has_media = device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsMediaAvailable")
            
            # Check if removable and actually has files
            if device_has_media:
                #logger.info("Drive:" + str(device_is_drive))
                #logger.info("Removable:" + str(device_is_removable))
                #logger.info("Mounted: " + str(device_is_mounted))
                #logger.info("Has media:" + str(device_has_media))
                #logger.info("Interface:" + str(device_interface))

                if len(device_mount_paths) > 0:
                    drive_path = str(device_mount_paths[0])
                    #logger.info("Mount point: " + str(device_mount_paths[0]))

                    #logger.info(device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsPartition"))
                    #logger.info("Device file: " + str(device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")))
                    #logger.info(device_props.Get('org.freedesktop.UDisks.Device', "PartitionLabel"))
                    drive_vendor = device_props.Get('org.freedesktop.UDisks.Device', "DriveVendor")
                    drive_model = device_props.Get('org.freedesktop.UDisks.Device', "DriveModel")

                    drive_name = (str(drive_vendor) + ' - ' + str(drive_model) if device_interface == 'usb' else 'SD Card');

                    drive_info = {
                        'name': drive_name,
                        'path': drive_path,
                        'id': drive_id,
                    }
                    drive_id += 1
                    detected_drives.append(drive_info)

        #logger.info("*** DEVICE END ***")

    #logger.info(detected_drives)
    #logger.info("Enumerating drives COMPLETE")
    #logger.info("")
    #logger.info("")

    return detected_drives



@csrf_exempt
def usb_file_select():
    """
    Display the jstree for the attatched USB drives
    """
    is_drive = False

    if len(list_usb_drives()) > 0:
        is_drive = True

    return is_drive


def list_dir(path, name='USB', is_root=False, limit_to_type=None):
    """
    Take a path and contructs a dictionary of its contents compatible with jstree
    """
    if path is not None:
        if path[-1] != '/':
            path = path + '/'
        
        if is_root:
            results = {
                'id': base64.urlsafe_b64encode(bytes(path)),
                'text': name,
                'children': []
            }
        else:
            results = []

        fs = FileSystemStorage(location=path)
        dir_list, file_list = fs.listdir(unicode(path))

        for directory in dir_list:
            try:
                if '?' in directory:
                    raise Exception("invalid file")
                has_children = False
                # daveh - check here is child files are valid?
                if os.listdir(path + directory):
                    has_children = True
                child = {
                    'id': base64.urlsafe_b64encode(bytes(path + directory)),
                    'text': directory,
                    'children': has_children,
                }
                if is_root:
                    results['children'].append(child)
                else:
                    results.append(child)

            except Exception as e:
                #not added if cannot encode path, illegal chars
                pass
            
        for filename in file_list:
            try:
                if '?' in filename:
                    raise Exception("invalid file")
                if limit_to_type is not None:
                    for ftype in limit_to_type:
                        if not filename.lower().endswith(ftype.lower()):
                            raise Exception("filetype not allowed")
                encode_test = bytes(path + filename)

                file_size = os.path.getsize(path + filename) if os.path.isfile(path + filename) else ''

                child = {
                    'id': base64.urlsafe_b64encode(encode_test),
                    'text': filename,
                    'filesize': file_size,
                    'icon': 'jstree-file'
                }
                if is_root:
                    results['children'].append(child)
                else:
                    results.append(child)

            except Exception as e:
                #not added if cannot encode path, illegal chars
                pass

        return results
    else:
        return None


@csrf_exempt
def usb_import(data, metadata, async=False, microsite=False):
    """
    Accept POST containing an ID list. 
    Import files from that USB drive found to match each ID.
    """
    all_results = {}
    import_list = []
    importJobID = None
    site = site = type('obj', (object,), { 'micrositeURL': '', 'storageLocation': ''}) #placeholder obj (bugfix)
    try:
        for item in data:
            path = base64.urlsafe_b64decode(item.encode('utf8'))
            if async:
                imp = Importer(path, copy_to_preload=True, metadata=metadata, asynchronous=async, is_preloaded=True)
            else:
                site = Importer(path, copy_to_upload=True, metadata=metadata, isMicrosite=microsite)
            if async:
                importJobID = imp.asyncProcessID

    except Exception as e:
        json_displayed = {"result" : 'error', "type": "usb_removed"}
    else:
        if async and imp and (imp.usbError or imp.outOfSpaceError):
            if imp.usbError:
                json_displayed = {"result" : 'error', "type": "usb_removed"}
            else:
                json_displayed = {"result" : 'error', "type": "out_of_space"}
        elif not async and site and site.outOfSpaceError:
            json_displayed = {"result" : 'error', "type": "out_of_space"}
        else:
            json_displayed = {"result" : 'success', 'importJobID': importJobID, 'micrositeURL': site.micrositeURL, 'storageLocation': site.storageLocation }
    return json_displayed

def usb_response(path='/', filetypes=None):
    """
    Construct and object for the contents of USB drives
    """
    all_results = []
    if(path == '/' or path == '#'): #hash appears to be passed as root node for jstree
        for usb_drive in list_usb_drives():
            usb_path = usb_drive.get('path', None)
            usb_name = usb_drive.get('name', 'USB')
            usb_id = usb_drive.get('id', None)
            results = list_dir(path=usb_path, name=usb_name, is_root=True, limit_to_type=filetypes)
            all_results.append(results)
    else:
        root_encode_ok = True
        try: #try to catch a problem where folder to be expanded contains invalid characters.
            path = base64.urlsafe_b64decode(path.encode('utf8'))
            #path = base64.b64decode(path)
        except Exception as e:
            root_encode_ok = False
            pass
        if root_encode_ok:
            all_results = list_dir(path=path, limit_to_type=filetypes)
    return all_results

