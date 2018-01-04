/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //* Home controller 
    ////////////////////////////////////////
    angular.module('updateControllers', []).controller("UpdaterCtrl", ['$scope', 'Settings', 'toaster', 'APP_EVENTS', '$rootScope', 'FIELD_VAL', 'userService', '$window', 'Patches',
        function ($scope, Settings, toaster, APP_EVENTS, $rootScope, FIELD_VAL, userService, $window, Patches) {
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.current_version = 0;
            //$scope.uploadForm = {};
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.working = false;
            $scope.file_title_mapping = [];
            $scope.actual_files = [];
            $scope.fileErrors = [];
            $scope.formScope = {};

            $scope.setFormScope = function (scope) {
                $scope.formScope = scope;
            }

            if ($scope.user.is_authenticated) {
                if ($scope.user.is_superuser === false) {
                    userService.authFromToken().$promise.then(function () {
                        $scope.user = userService.get();
                    });
                }
                //do protected method
            }
            $scope.$on('$destroy', function () {
                $(window).off('beforeunload');
            });
            $(window).on('beforeunload', function (e) {
                if ($scope.formScope.uploadForm && $scope.formScope.uploadForm.$dirty) {
                    var message = gettext('If you leave this page all unsaved changes will be lost, are you sure?');
                    e.returnValue = message;
                    return message;
                }
            });
            $scope.$on('$locationChangeStart', function (event) {
                if ($scope.formScope.uploadForm) {
                    if (!$scope.formScope.uploadForm.$dirty) return;
                    var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                    if (!answer) {
                        event.preventDefault();
                    }
                }
            });
            //reset the file list on each click as reselecting same file again wont trigger 'fileSelected'
            $scope.clearFileSelection = function ($event) {
                $event.target.value = null;
                $scope.actual_files = [];
                if ($scope.uploadForm) { $scope.uploadForm.$setDirty(); }
            };
            $scope.onFileSelect = function ($files) {
                $scope.file_title_mapping = [];
                $scope.fileErrors = [];
                //create a mapping for each fileobject, to new title.
                for (var i = 0; i < $files.length; i++) {
                    if ($files[i].name.length > FIELD_VAL.filenameMax) {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum length of the filename is %(maxchars)s."), { filename: $files[i].name, maxchars: FIELD_VAL.filenameMax }, true));
                    } else if ($files[i].size > FIELD_VAL.fileSizeMax) {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum size of a file is %(maxsize)s."), { filename: $files[i].name, maxsize: $filter('filesizeformat')(FIELD_VAL.fileSizeMax) }, true));
                    } else if ($files[i].name.toLowerCase().split('.').pop() !== 'zip') {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : Only ZIP files are allowed"), { filename: $files[i].name }, true));
                    } else {
                        $scope.actual_files.push($files[i]);
                        var title = $files[i].name.substr(0, $files[i].name.lastIndexOf("."));;
                        $scope.file_title_mapping.push({
                            'file_index': i,
                            'filename': $files[i].name,
                            'title': title,
                            'upload_status': '0 %',
                            'zip_status': 'Pending',
                            'import_status': 'Pending',
                            'upload_total': $files[i].size,
                            'uploaded': false,
                            'error': false
                        });
                    }
                }
                $scope.formScope.uploadForm.$setDirty();
            };
            $scope.save = function (metadata, category) {
                //var answer = confirm('The Application Update will be uploaded, applied and the device will restart.  All connections to the device will be terminated. Are you sure you want to proceed?')
                //if (answer) {
                    $scope.working = true;
                    $('.uploadcomplete-false').css('display', 'block');

                    var formobj = {};
                    formobj.file = $scope.actual_files[0];

                    Patches.save(formobj, function (success) {
                        $scope.file_title_mapping[0].upload_completed = true;
                        $scope.file_title_mapping[0].uploaded = true;
                        toaster.pop('success', gettext("The device will now restart & the update will be applied.\nDo not disrupt the update process and make sure the device is plugged into an electrical outlet or has at least 80% battery remaining."));
                        $scope.working = false;
                        //$scope.$location.path('/managepreloaded');
                        //$scope.$destroy(); //call destroy to unbind the dirty bit
                    }, function (fail) {
                        if (fail.message) {
                            $scope.actual_files = [];
                            $scope.uploadForm.$setDirty();
                        }
                        //toaster.pop('success', gettext("An error occurred"));
                        $scope.working = false;
                    });
                //}
            };
        }
    ]);
}());