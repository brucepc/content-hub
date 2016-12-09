/// <reference path="../../angularjs/angular.js" />
/// <reference path="../../angularjs/angular-route.min.js" />
var app = angular.module('ecApp', [
    'ng.django.urls', 'ecServices', "hubControllers", "commonControllers", "ecDirectives", 'ecFilters', "ngRoute", 'ngResource', 'toaster', 'ngCookies', 'LocalStorageModule', 'ngTouch', 'blockUI', 'xeditable', 'angularFileUpload',
])

app.config(function ($httpProvider, $interpolateProvider, $routeProvider, blockUIConfig) {

    $httpProvider.interceptors.push('ecInterceptor');

    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.headers.post['Access-Control-Allow-Origin'] = '*';
    $httpProvider.defaults.headers.put['Access-Control-Allow-Origin'] = '*';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';

    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');


    blockUIConfig.message = gettext("Please Wait...");

    blockUIConfig.template = '<div class="block-ui-overlay"></div><div class="cg-busy-default-wrapper block-ui-message-container" aria-live="assertive" aria-atomic="true">' +
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
        if (config.url.match(/^\/rest\/settings($|\/).*/) || config.url.match(/^\/rest\/tokenauth($|\/).*/)) {
            return false; // ... don't block it.
        }
    };

    $routeProvider.when('/', {
        templateUrl: '/angularviews/hub/home.html'
    }).when('/login', {
        templateUrl: '/angularviews/login.html',
        controller: 'LoginCtrl'
    }).when('/logout', {
        template: ' ',
        redirectTo: '/',
        controller: 'LogoutCtrl'
    }).when('/404', {
        templateUrl: '/angularviews/hub/404.html'
    }).otherwise({ redirectTo: '/404' });
}).run(
    function ($http, $cookies, $rootScope, $location, userService) {
        $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
        // Add the following two lines
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        $rootScope.$on('$locationChangeStart', function (event, next, current) {

            var user = userService.get();
            if (next.indexOf('?createtile') > -1) {
                if (user.isAdmin()) {
                    //ok to do this
                }
                else {
                    $location.path('/').search('');
                }
            }
        });

    });