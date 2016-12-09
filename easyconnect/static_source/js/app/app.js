/// <reference path="../../angularjs/angular.js" />
/// <reference path="../../angularjs/angular-route.min.js" />
var app = angular.module('ecApp', [
    'ng.django.urls', 'ecControllers', "commonControllers", 'ecFilters', 'ecServices', "ecDirectives", "ngRoute", 'ngResource', 'RecursionHelper', 'toaster', 'xeditable', 'ngTagsInput', 'ngCookies', 'ngDragDrop', 'LocalStorageModule', 'ngTouch', 'blockUI', 'angularFileUpload', 'ngSanitize', 'blueimp.fileupload',
])

app.config(['$httpProvider', '$interpolateProvider', '$routeProvider', '$resourceProvider', 'blockUIConfig', 'fileUploadProvider',
    function ($httpProvider, $interpolateProvider, $routeProvider, $resourceProvider, blockUIConfig, fileUploadProvider) {
   
    var onIE9 = function () {
        return navigator.sayswho === "MSIE 9";
    };

    $httpProvider.interceptors.push('ecInterceptor');

    if (onIE9()) {
        delete $httpProvider.defaults.headers.common['X-Requested-With'];
        fileUploadProvider.defaults.redirect = window.location.href.replace(
            /\/[^\/]*$/,
            '/static/jquery-file-upload/cors/result.html?%s'
        );
    } else {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.headers.post['Access-Control-Allow-Origin'] = '*';
    $httpProvider.defaults.headers.put['Access-Control-Allow-Origin'] = '*';
    }
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';

    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    blockUIConfig.message = gettext("Please Wait...");

    blockUIConfig.template = '<div class="block-ui-overlay" style="cursor: default !important;"></div><div class="cg-busy-default-wrapper block-ui-message-container" aria-live="assertive" aria-atomic="true">' +
           '<div class="cg-busy-default-sign">' +
                 '<div class="cg-busy-default-spinner">' +
                    '<div class="bar1"></div>' +
                    '<div class="bar2"></div>' +
                    '<div class="bar3"></div>' +
                    '<div class="bar4"></div>' +
                    '<div class="bar5"></div>' +
                    '<div class="bar6"></div>' +
                    '<div class="bar7"></div>' +
                    '<div class="bar8"></div>' +
                    '<div class="bar9"></div>' +
                    '<div class="bar10"></div>' +
                    '<div class="bar11"></div>' +
                    '<div class="bar12"></div>' +
                '</div>' +
        '<div class="cg-busy-default-text">{{ state.message }}</div>' +
        '</div></div>';

    // Tell the blockUI service to ignore certain requests
    blockUIConfig.requestFilter = function (config) {
        if (
            config.url.match(/^\/rest\/settings($|\/).*/) ||
            config.url.match(/^\/rest\/tokenauth($|\/).*/) ||
            config.url.match(/^\/rest\/packages($|\/).*/)
            ) {
            return false; // ... don't block it.
        }
    };

    //only in v1.3.0
    //$resourceProvider.defaults.stripTrailingSlashes = false;

    var getTemplateForUpload = function () {
        if (onIE9())
            return '/angularviews/uploadIE9.html';

        return '/angularviews/upload.html';
    };

    $routeProvider.when('/', {
        templateUrl: '/angularviews/home.html'
    }).when('/login', {
        templateUrl: '/angularviews/login.html',
        controller: 'LoginCtrl'
    }).when('/logout', {
        template: ' ',
        redirectTo: '/',
        controller: 'LogoutCtrl'
    }).when('/lessons/', {
        templateUrl: '/angularviews/lessons.html',
        controller: 'LessonCtrl'
    }).when('/lessons/:Id', {
        templateUrl: '/angularviews/lesson_detail.html',
        controller: 'LessonCtrl'
    }).when('/library/', {
        templateUrl: '/angularviews/library.html',
        controller: 'LibraryCtrl',
        reloadOnSearch: false
    }).when('/library/upload', {
        templateUrl: getTemplateForUpload(),
        controller: 'UploadCtrl'
    }).when('/library/:id', {
        templateUrl: '/angularviews/upload.html',
        controller: 'ContentItemCtrl'
    }).when('/settings', {
        templateUrl: '/angularviews/settings.html',
        controller: 'SettingCtrl'
    }).when('/manage/tags', {
        templateUrl: '/angularviews/tags.html',
        controller: 'TagCtrl'
    }).when('/manage/categories', {
        templateUrl: '/angularviews/categories.html',
        controller: 'CategoryCtrl'
    }).when('/search/:term?', {
        templateUrl: '/angularviews/search.html',
        controller: 'SearchCtrl'
    }).when('/usb', {
        templateUrl: '/angularviews/usb.html',
        controller: 'UsbCtrl'
    }).when('/preload/up-load', {
        templateUrl: '/angularviews/preload-upload.html',
        controller: 'PreloadUploadCtrl'
    }).when('/preload/usb', {
        templateUrl: '/angularviews/preload-usb.html',
        controller: 'PreloadUsbCtrl'
    }).when('/non_existent_route_to_force_refresh', {
        templateUrl: '/angularviews/home.html',
        redirectTo: '/',
    }).when('/404', {
        templateUrl: '/angularviews/hub/404.html'
    }).otherwise({ redirectTo: '/404' });
}]).run(
    function ($http, $cookies, editableThemes, $rootScope, Settings, userService, $location, AUTH_EVENTS, APP_EVENTS, Utils, blockUI, localStorageService) {
        $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
        // Add the following two lines
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        angular.element(document).ready(function () {
            //console.log('starting...');
        });
       
        // overwrite submit button template
        editableThemes['default'].submitTpl = '<button type="submit" class="brandBtnColor"><span class="fa fa-check"></span></button>';
        editableThemes['default'].cancelTpl = '<button type="button" ng-click="$form.$cancel()"><span class="fa fa-times"></span></button>';
        editableThemes['default'].errorTpl = '<ul ng-show="$error" class="errorlist"><li class="errorArrow"></li><li ng-bind="$error"></li></ul>';

        

        $rootScope.$on('$locationChangeStart', function (event, next, current) {
            var storedUserType = localStorageService.get('authType') == 'true';
            if (storedUserType) {
                //is an admin, coming in direct to a url or via a refresh.
            }

            var user = userService.get();
            //route blocking for admin and student
            if (!(user.type == 'teacher')) {
                if (next.indexOf('/upload') > -1) {
                    $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                    Utils.executeFn(function () {
                        $location.path('/');
                    });
                }
                else if (next.indexOf('/library') > -1) {
                    if (user.isAdmin()) {
                        $location.path('/');
                        $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                    }
                    else {
                        //student
                        Settings.checkLibrary(function (response) {
                            if (response.library_hidden) {
                                Utils.executeFn(function () {
                                    $location.path('/');
                                    $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                                    $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                                }, true);
                            }
                        });
                    }
                }
                else if (next.indexOf('/manage') > -1) {
                    if (user.isAdmin()) {
                        $location.path('/');
                        $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                    }
                    else {
                        //student
                        $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                        Utils.executeFn(function () {
                            $location.path('/');
                        });
                    }
                }
                else if (next.indexOf('/lessons') > -1 && user.isAdmin()) {
                    if (user.isAdmin()) {
                        $location.path('/');
                        $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                    }
                    else {
                        //student
                        $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                        Utils.executeFn(function () {
                            $location.path('/');
                        });
                    }
                }
                else if (next.indexOf('/usb') > -1 && next.indexOf('preload/usb') == -1) {
                    if (user.isAdmin()) {
                        $location.path('/');
                        $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                    }
                    else {
                        //student
                        $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                        Utils.executeFn(function () {
                            $location.path('/');
                        });
                    }
                }
                else if (next.indexOf('/preload') > -1 && !user.isAdmin()) {
                        //student only
                        $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                        Utils.executeFn(function () {
                            $location.path('/');
                        });
                }
            }
            //route blocking for teacher
            else if (next.indexOf('/preload') > -1 && !user.isAdmin()) {
                $rootScope.$broadcast(AUTH_EVENTS.accessDenied);
                Utils.executeFn(function () {
                    $location.path('/');
                });
            }
        });

    });