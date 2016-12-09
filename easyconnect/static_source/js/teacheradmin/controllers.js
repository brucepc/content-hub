/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //* Home controller 
    ////////////////////////////////////////
    angular.module('taControllers', []).controller("HomeCtrl", ['$scope', 'Settings', 'toaster', 'APP_EVENTS', '$rootScope', 'FIELD_VAL', 'userService', '$window', 'Database',
        function ($scope, Settings, toaster, APP_EVENTS, $rootScope, FIELD_VAL, userService, $window, Database) {
            
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.SSID = '';
            $scope.resettingAccount = false;
            $scope.remoteManagement = false;
            // Aidan Commented out code below as per request from Bun 01-06-16
            //$scope.study = false;
            $scope.showServices = false;

            Database.getLatest().then(function(resp){
                $scope.lastBackup = resp;
            });

            $scope.restoreDatabase = function () {
                Database.restore().then(function(resp){
                    toaster.pop('success', 'Device will restart and Database will be restored');
	        });

            };

            $scope.toggleInternet = function () {
                Settings.toggleInternet(function (response) {
                    $scope.internet = response.internet > 0;
                    //refactored so message is clear to translators
                    var msg;
                    if ($scope.internet) {
                        msg = gettext("Internet Access Enabled");
                    }
                    else {
                        msg = gettext("Internet Access Disabled");
                    }
                    toaster.pop('success', msg);
                    $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                });
            };

            if ($scope.user.is_authenticated) {
                if ($scope.user.is_superuser === false) {
                    userService.authFromToken().$promise.then(function () {
                        $scope.user = userService.get();
                        activate();
                    });
                }
            }
            Settings.getSSID(function (response) {
                $scope.SSID = response.ssid;
            });
            $scope.updateSSID = function (ssid, form) {
                Settings.setSSID({ 'ssid': ssid }, function (response) {
                    if (response.success !== 'True')
                        toaster.pop('error', gettext("Problem updating SSID"));
                });
            };

            $scope.confirmSSIDChange = function () {
                return $window.confirm(gettext("Changing the SSID will terminate all connections to this device. Are you sure you want to proceed?"));
            };

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

            $scope.resetTeacherAccount = function () {
                var del = $window.confirm(gettext("Are you sure you want to reset the Teacher account?"));
                if (del) {
                    $scope.resettingAccount = true;
                    Settings.resetTeacherAccount({}, function (response) {
                        $scope.$apply(function () {
                            $scope.resettingAccount = false;
                        });
                        if (response.success !== 'True') {
                            toaster.pop('error', gettext("The teacher account was not reset."));
                        }
                        else {
                            toaster.pop('success', gettext("Teacher account reset."));
                        }
                    });
                }
            }

            $scope.toggleRemoteManagement = function () {
                Settings.toggleRemoteManagement({ "remotemanagement" : $scope.remoteManagement ? "off" : "on" }, function (response) {
                    if (angular.isDefined(response.remotemanagement)) {
                        $scope.remoteManagement = response.remotemanagement > 0;
                        //refactored so message is clear to translators
                        var msg;
                        if ($scope.remoteManagement) {
                            msg = gettext("Remote Management Enabled");
                        }
                        else {
                            msg = gettext("Remote Management Disabled");
                        }
                        toaster.pop('success', msg);
                        $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                    } else {
                        toaster.pop('error', gettext("Error occurred Enabling/Disabling Remote Management"));
                    }
                });
            };

            //var StudyResponseCodes = {
            //    'SUCCESS' : 0,
            //    'SERVICE_CURRENT_STATUS_START': 1,
            //    'SERVICE_CURRENT_STATUS_STOP': 2,
            //    'ILLEGAL_ARGUMENT_NUMBER': 11,
            //    'ILLEGAL_ARGUMENT_SERVICE_OPERATION' : 12,
            //    'ILLEGAL_ARGUMENT_SERVICE_NAME': 13,
            //    'SERVICE_NOT_INSTALLED': 14,
            //    'SERVICE_IS_ALREADY_STARTED': 15,
            //    'SERVICE_IS_ALREADY_STOPPED': 16,
            //    'ERROR_STARTING_SERVICE': 17,
            //    'ERROR_STOPPING_SERVICE': 18,
            //    'ERROR_CHECKING_CHANGING_CONFIG_FILE': 19,
            //    'ERROR_FINDING_CONFIG_FILE': 20,
            //    'SERVICE_ALREADY_ENABLED': 21,
            //    'SERVICE_ALREADY_DISABLED': 22
            //}

            //$scope.toggleStudy = function () {
            //    Settings.toggleStudy(function (response) {
            //        var msg, msgType = 'success';
            //        switch (+response.study) {
            //            case StudyResponseCodes.SERVICE_CURRENT_STATUS_START:
            //                $scope.study = true;
            //                msg = gettext("Intel Education Study Enabled");
            //                break;
            //            case StudyResponseCodes.SERVICE_CURRENT_STATUS_STOP:
            //                $scope.study = false;
            //                msg = gettext("Intel Education Study Disabled");
            //                break;
            //            default:
            //                console.log("Study response code: " + response.study || '');
            //                msg = gettext("An error occurred enabling/disabling Study");
            //                msgType = 'error';
            //        }

            //        toaster.pop(msgType, msg);
            //        if (msgType == 'success') $rootScope.$broadcast(APP_EVENTS.settingsChanged);

            //    });
            //};

            function activate() {
                if ($scope.user.is_superuser) {
                    //alert("is super user");
                    Settings.getCAPVersion().$promise.then(function (resp) {
                        //alert("cap version " + resp.version);                        
                        if (resp.version && +resp.version > 1) {
                            //alert("CAP version true");
                            $scope.showServices = true;



                            //Settings.checkStudy().$promise.then(function (response) {
                            //    switch (+response.study) {
                            //        case StudyResponseCodes.SERVICE_CURRENT_STATUS_START:
                            //            $scope.study = true;
                            //            break;
                            //        case StudyResponseCodes.SERVICE_CURRENT_STATUS_STOP:
                            //            $scope.study = false;
                            //            break;
                            //        default:
                            //            $scope.study = false;
                            //            var msg = gettext("An error occurred getting Study status");
                            //            toaster.pop('error', msg);
                            //    };
                            //});

                            Settings.checkRemoteManagement().$promise.then(function (response) {
                                $scope.remoteManagement = response.remotemanagement > 0;
                            });
                        } else {
                            $scope.showServices = false;
                        }
                    });
                } else {
                    $scope.showServices = false;
                }
            };
        }
    ]).controller("ChangePaswordCtrl", ["$scope", 'Settings', 'toaster', 'FIELD_VAL', '$location', 'Utils', 'userService', function ($scope, Settings, toaster, FIELD_VAL, $location, Utils, userService) {
        $scope.FIELD_VAL = FIELD_VAL;
        $scope.changepass = {};

        $scope.update = function (model, form) {
            if (form.$valid) {
                var un = userService.get().username;
                var pw = model.newPassword;
                Settings.updatePassword(model, function (response) {
                    if (response.success == 'True') {
                        toaster.pop('success', gettext("Password updated successfully"));
                        userService.logout();
                        userService.login(un, pw);
                        Utils.executeFn(function () {
                            $location.path('/');
                        });
                    }
                    else {
                        var message = response.message || gettext("Problem updating Password");
                        toaster.pop('error', message);
                    }
                });
            }
        }

        $scope.cancel = function (form) {
            $scope.changepass = {};
            form.$setPristine();
            $location.path('/');
        }
    }]);



}());