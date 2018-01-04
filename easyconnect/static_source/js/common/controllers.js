/// <reference path="../../angularjs/angular.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //* Main wrapper controller to wrap common functionality
    ////////////////////////////////////////
    angular.module('commonControllers', []).controller("MainCtrl", ['$scope', '$window', 'userService', '$location', 'Settings', 'toaster', 'AUTH_EVENTS', '$interval', 'APP_EVENTS', 'VERSION',
        function ($scope, $window, userService, $location, Settings, toaster, AUTH_EVENTS, $interval, APP_EVENTS, VERSION) {

            $scope.$location = $location;
            $scope.user = null;
            $scope.working = false;
            $scope.battery = 99;
            $scope.currentVersion = VERSION.current;

            $scope.showNavContainer = false;
            $scope.showSubManageMenu = false;

            var getCurrentSettings = function () {
                $scope.user = userService.get();
                Settings.checkInternet(function (response) {
                    $scope.internet = response.internet > 0;
                    $scope.battery = response.battery;
                });
            };

            var batterychecktimmer = $interval(function () {
                Settings.checkInternet(function (response) {
                    $scope.internet = response.internet > 0;
                    $scope.battery = response.battery;
                });
            }, 600000 /* 10 mins*/);

            getCurrentSettings();

            $scope.$on(APP_EVENTS.settingsChanged, function () {
                getCurrentSettings();
            });

            $scope.$on(AUTH_EVENTS.authenticationChanged, function () {
                getCurrentSettings();
            });

            $scope.$on(AUTH_EVENTS.accessDenied, function () {
                toaster.pop('warning', gettext("You do not have access to the requested page"));
            });

            $scope.$on('token-timeout', function () {
                userService.logout();
            });

            $scope.$on("$destroy", function (event) {
                $interval.cancel(batterychecktimmer);
            });
            /*
            $scope.switchUserView = function (view) {
                Settings.toggleViewType({ 'type': view }, function (response) {
                    $scope.user.type = view;
                    console.log(view);
                    $location.path('/non_existent_route_to_force_refresh');
                });
            };
            */
            /*
            Settings.toggleViewType({ 'type': view }, function (response) {
                $scope.user.type = view;
                if (view == 'admin') {
                    $location.path('/');
                }
                $window.location.reload(true);
            });
            */

            $scope.showManageMenu = function (event) {
                $scope.showSubManageMenu = true;
            };

            $scope.hideManageMenu = function (event) {
                $scope.showSubManageMenu = false;
                $scope.showNavContainer = false;
            };

            $scope.toggleNavContainer = function () {
                $scope.showNavContainer = !$scope.showNavContainer;
            };
        }
    ]).controller("LoginCtrl", ["$scope", 'userService', '$routeParams', '$rootScope', 'AUTH_EVENTS', 'Utils', '$location', 'Settings', '$window',
    function ($scope, userService, $routeParams, $rootScope, AUTH_EVENTS, Utils, $location, Settings, $window) {
        $scope.login = function (username, password, form) {
            if (username && password) {
                userService.login(username, password).$promise.then(function (success) {
                    Utils.executeFn(function () {
                        $rootScope.$broadcast(AUTH_EVENTS.authenticationChanged);
                        var redirectTo = '/'
                        if ($routeParams.next) {
                            if ($location.path() != $routeParams.next)
                                redirectTo = $routeParams.next;
                        }
                        $location.path(redirectTo);
                    }, true);
                }, function (fail) {
                    if (fail.status != 0)
                        form.$setValidity('loginfailed', false);
                });
            } else {
                if (!username) {
                    form.username.$setValidity('required', false);
                    form.username.$submitted = true;
                }
                if (!password) {
                    form.password.$setValidity('required', false);
                    form.password.$submitted = true;
                }
            }
        };

    }]).controller("LogoutCtrl", ["$scope", 'userService', '$routeParams', '$rootScope', 'AUTH_EVENTS', 'Utils', '$location', 'Settings', '$window',
        function ($scope, userService, $routeParams, $rootScope, AUTH_EVENTS, Utils, $location, Settings, $window) {
            userService.logout();
            /*
            Settings.toggleViewType({ 'type': 'teacher' }, function (response) {
                
            });
            */
            Utils.executeFn(function () {
                $location.path($routeParams.next || '/');
                //$window.location.reload(true);
            });
            $rootScope.$broadcast(AUTH_EVENTS.authenticationChanged);
        }
    ]);
}());