/// <reference path="../../angularjs/angular.js" />
(function () {
    angular.module('ecApp').constant('AUTH_EVENTS', {
        'accessDenied': 'user-access-denied',
        'authenticationChanged': 'user-authentication-changed'
    }).constant('APP_EVENTS', {
        'checkedItemsChanged': 'checked-items-changed',
        'clearCheckedItems': 'clear-checked-items',
        'featuredContentChanged': 'featured-content-changed',
        'settingsChanged': 'settings-changed',
        'usbNotFound' : 'usb-not-found'
    }).constant('FIELD_VAL', {
        'categoryMax': 50,
        'tagMax': 25,
        'contentItemMax': 100,
        'lessonMax': 100,
        'filenameMax': 80,
        'tilenameMax': 50,
        'tileURLMax': 100,
        'tileIconMax' : 256000,
        'tileDefaultCount': 1,
        'tileDefaultCountTeacher': 2,
        'defaultTileIcon': 'images/default_tile_icon.png',
        'fileSizeMax': 2147483648,
        //'passwordPattern': '^[a-zA-Z0-9]{6,}$',
        'passwordPattern': '^.{6,}$', //minimum 6, any character
        'ssidMax' : 32
    }).constant('TOAST_TYPES', {
        'success': 'success',
        'warning': 'warning',
        'error': 'error'
    }).constant('VERSION', {
        'current': '1.8.18'
    });
}());