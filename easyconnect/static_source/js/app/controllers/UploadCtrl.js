/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    angular.module('ecControllers').controller("UploadCtrl", ["$scope", 'ContentItems', 'toaster', 'FIELD_VAL', 'Utils', '$routeParams', '$filter', 'localStorageService', 'blockUI',
        function ($scope, ContentItems, toaster, FIELD_VAL, Utils, $routeParams, $filter, localStorageService, blockUI) {
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.content = {};
            $scope.content_file = null;
            $scope.working = false;
            $scope.file_title_mapping = [];
            $scope.actual_files = [];
            $scope.category = 0;
            $scope.fileErrors = [];

            $scope.$on('$destroy', function () {
                $(window).off('beforeunload');
            });

            $(window).on('beforeunload', function (e) {
                if ($scope.uploadForm.$dirty) {
                    var message = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'));
                    e.returnValue = message;
                    return message;
                }
            });

            $scope.selectCategory = function (selectedCategory) {
                $scope.category = selectedCategory.id
                $scope.uploadForm.$setDirty();
                $scope.$apply();
            };

            $scope.clearCategory = function () {
                $scope.category = 0;
                $scope.uploadForm.$setDirty();
                $scope.$apply();
            };

            //reset the file list on each click as reselecting same file again wont trigger 'fileSelected'
            $scope.clearFileSelection = function ($event) {
                $event.target.value = '';
                $scope.actual_files = [];
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
                    } else {
                        $scope.actual_files.push($files[i]);
                        var title = $files[i].name.substr(0, $files[i].name.lastIndexOf("."));;
                        $scope.file_title_mapping.push({ 'filename': $files[i].name, 'title': title, 'uploaded': false, 'error': false });
                    }
                }
                $scope.uploadForm.$setDirty();
            };

            $scope.save = function (metadata, category) {
                $('.uploadcomplete-false').css('display', 'block');
                var total_count = $scope.actual_files.length;

                _.each($scope.actual_files, function (single_file, index) {
                    var formobj = {};
                    var title = _.find($scope.file_title_mapping, function (map) {
                        return single_file.name == map.filename
                    }).title;
                    formobj.metadata = angular.copy(metadata);
                    if (+$scope.category > 0) {
                        formobj.metadata['categories'] = $scope.category;//add the category
                    }
                    formobj.metadata['title'] = title; //add the updated title
                    formobj.file = single_file;
                    //if (form.$valid) {
                    $scope.working = true;
                    $scope.uploadPromise = ContentItems.save(formobj, function (success) {
                        _.find($scope.file_title_mapping, function (map) {
                            if (single_file.name == map.filename) {
                                map.uploaded = true;
                            }
                        });
                        toaster.pop('success', gettext("Item successfully uploaded"));
                        total_count = total_count - 1;
                        if (total_count <= 0) {
                            $scope.working = false;
                            $scope.$destroy(); //call destroy to unbind the dirty bit
                            var redirectTo = Utils.createLibraryRedirect($routeParams);
                            $scope.$location.url(redirectTo);
                        }
                    }, function (fail) {
                        _.find($scope.file_title_mapping, function (map) {
                            if (single_file.name == map.filename) {
                                map.error = true;
                            }
                        });
                        total_count = total_count - 1;
                        if (total_count <= 0) {
                            $scope.working = false;
                        }
                    });
                    //}
                });//endeach

            };

            if (navigator.sayswho === "MSIE 9") {

                $("#fileupload").fileupload({
                    dataType: 'json',
                    maxFileSize: FIELD_VAL.fileSizeMax,
                    withCredentials: true,
                    autoUpload: false,
                    url: '/rest/ie9contentitems/',
                    forceIframeTransport: true,
                    add: function (e, data) {
                        var file = data.files[0];
                        $scope.content_file = null;
                        $scope.fileErrors = [];
                        if (file.name.length > FIELD_VAL.filenameMax) {
                            $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum length of the filename is %(maxchars)s."), { filename: file.name, maxchars: FIELD_VAL.filenameMax }, true));
                        } else if (file.size > FIELD_VAL.fileSizeMax) {
                            $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum size of a file is %(maxsize)s."), { filename: file.name, maxsize: $filter('filesizeformat')(FIELD_VAL.fileSizeMax) }, true));
                        } else {
                            $scope.filename = file.name;
                            $scope.content_file = file;
                            var title = file.name.substr(0, file.name.lastIndexOf("."));;
                            $scope.content.title = title;
                            $('#submitBtn').on('click', function (e) {
                                e.preventDefault();
                                $scope.working = true;
                                blockUI.start();
                                data.submit();
                            });
                        }
                        $scope.uploadForm.$setDirty();
                        $scope.$apply();
                    },
                    submit: function (e, data) {
                        var $this = $(this);

                        data.formData = [{
                            name: 'authenticity_token',
                            value: localStorageService.get('authorizationData')['token']
                        },
                        {
                            name: 'title',
                            value: $scope.content.title
                        },
                        {
                            name: 'description',
                            value: $scope.content.description
                        }];

                        if (+$scope.category > 0) {
                            var arr = [];
                            arr.push($scope.category)
                            data.formData.push({
                                name: 'categories',
                                value: arr
                            });//add the category
                        }

                        var tmp = [];
                        var array = $scope.content.tags;
                        if (array && array.length > 0) {
                            for (var i = 0, len = array.length; i < len; i++) {
                                tmp.push(typeof array[i] === 'object' ? array[i].id : array[i]);
                            }
                            data.formData.push({
                                name: 'tags',
                                value: tmp
                            });
                        }
                    },
                    done: function (e, data) {
                        //console.log("done");

                        var errors = data.result.Errors;
                        if (errors != null && errors.length > 0) {
                            for (var i = 0; i < errors.length; i++) {
                                toaster.pop('error', errors[0]);
                            }
                        } else {
                            successfulUpload()
                        }
                        $scope.working = false;
                        blockUI.stop();
                    },
                    error: function (e) {
                        //console.log("error");
                        $scope.working = false;
                        blockUI.stop();
                        if (e.status === 200 || e.status === 201) {
                            successfulUpload()
                        } else {
                            toaster.pop('error', e.statusText);
                        }
                    }
                });
            };

            var successfulUpload = function () {
                toaster.pop('success', gettext("Item successfully uploaded"));
                $scope.$destroy(); //call destroy to unbind the dirty bit
                var redirectTo = Utils.createLibraryRedirect($routeParams);
                $scope.$location.url(redirectTo);
            };

            $scope.save_ie9 = function () {
                //do nothing
            };
        }]);
}());