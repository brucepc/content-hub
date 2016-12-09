/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    angular.module('ecControllers').controller("ManagePreloadedCtrl", ["$scope", "$rootScope", 'toaster', "Packages", "ContentManagement", '$window', 'APP_EVENTS', 'SharedData',
    function ($scope, $rootScope, toaster, Packages, ContentManagement, $window, APP_EVENTS, SharedData) {

        $scope.packages = [];
        $scope.selectAll = [];

        $scope.checkedPackages = {};

        $scope.allPackagesSelected = false;
        $scope.selectedTeacherContent = false;
        $scope.selectedCategories = false;

        $scope.disableCheck = true;

        $scope.hascontent = false;
        $scope.hascategories = false;
        $scope.checkContentEnabled = function () {
            return !$scope.hascontent;
        }
        $scope.checkCategoriesEnabled = function () {
            return !$scope.hascategories;
        }

        var refreshDeleteBoxes = function () {
            if ($scope.user.is_authenticated) {
                ContentManagement.checkteachercontent(function (response) {
                    if (response.hasdata)
                        $scope.hascontent = true;
                });
                ContentManagement.checkcategories(function (response) {
                    if (response.hasdata)
                        $scope.hascategories = true;
                });
            }
        }
        refreshDeleteBoxes();

        var refreshlist = function () {
            $scope.checkedPackages = {};
            $scope.packages = [];
            if ($scope.user.is_authenticated) {
                Packages.query(function (response) {
                    $scope.packages = response;
                    //initialize the selected packages tracker
                    _.each(response, function (val, key) {
                        $scope.checkedPackages[key] = false;
                    });
                    if ($('#packages-select-all')[0]) {
                        $('#packages-select-all')[0].checked = false;
                    }
                    $scope.allPackagesSelected = false;
                    //$('#packages-select-all').attr('disabled', !($scope.packages.length > 0));
                });
            }
        };

        $scope.isdisabledPreloaded = function () {
            return !($scope.packages.length && $scope.packages.length > 0);
        }

        refreshlist();

        $scope.batchDelete = function () {
            if ($scope.deletePackagesEnabled()) {
                var todelete = [];
                _.any($scope.checkedPackages, function (val, key) {
                    if (val === true)
                        todelete.push($scope.packages[key].id);
                });

                if (todelete.length) {
                    var del = $window.confirm(gettext("Are you sure you want to delete these packages?"));
                    if (del) {
                        Packages.bulkdelete({ 'ids': todelete }, function () {
                            toaster.pop('success', gettext("Packages deleted"));
                            refreshlist();
                            refreshDeleteBoxes();
                        });
                    }
                } else {
                    toaster.pop('warning', gettext("No packages selected"));
                }
            }
        }

        $scope.ischecked_teacher = function () {
            return $scope.selectedTeacherContent;
        }

        $scope.deleteTeacherContent = function () {
            if ($scope.ischecked_teacher()) {
                if ($scope.selectedTeacherContent) {
                    var del = $window.confirm(gettext("Are you sure you want to delete all teacher content?"));
                    if (del) {
                        ContentManagement.deleteteachercontent({}, function () {
                            toaster.pop('success', gettext("Teacher content deleted"));
                            //uncheck
                            $scope.selectedTeacherContent = false;
                            $scope.hascontent = false;
                            //update the categories deletebox
                            refreshDeleteBoxes();
                        });
                    }
                } else {
                    toaster.pop('warning', gettext("Nothing selected"));
                }
            }
        }



        $scope.checkAllButton = function () {
            var packagecount = 0;
            var selectedcount = 0;
            _.each($scope.packages, function (val, key) {
                packagecount++;
            });
            _.each($scope.checkedPackages, function (val, key) {
                if (val == true)
                    selectedcount++;
            });

            if (packagecount > 0 && packagecount == selectedcount) {
                $scope.allPackagesSelected = true;
                $('#packages-select-all')[0].checked = true;
            }
            else {
                $('#packages-select-all')[0].checked = false;
                $scope.allPackagesSelected = false;
            }
        }

        $scope.ischecked_categories = function () {
            return $scope.selectedCategories;
        }

        $scope.deleteUnusedCategories = function () {
            if ($scope.ischecked_categories()) {
                if ($scope.selectedCategories) {
                    var del = $window.confirm(gettext("Are you sure you want to delete all unused categories?"));
                    if (del) {
                        ContentManagement.deletecategories({}, function () {
                            toaster.pop('success', gettext("Unused categories deleted"));
                            //uncheck
                            $scope.selectedCategories = false;
                            $scope.hascategories = false;
                        });
                    }
                } else {
                    toaster.pop('warning', gettext("Nothing selected"));
                }
            }
        }

        $scope.checkToggleCategories = function () {
            $scope.selectedCategories = !$scope.selectedCategories;
        }
        
        $scope.deletePackagesEnabled = function () {
            return _.any($scope.checkedPackages, function (val, key) {
                return val;
            });
        }

        $scope.checkToggleSelectAll = function () {
            $scope.allPackagesSelected = !$scope.allPackagesSelected;
            if ($scope.allPackagesSelected) {
                _.each($scope.checkedPackages, function (val, key) {
                    $scope.checkedPackages[key] = true;
                });
            }
            else {
                _.each($scope.checkedPackages, function (val, key) {
                    $scope.checkedPackages[key] = false;
                });
            }
        }
        $scope.checkToggleTeacherContent = function () {
            $scope.selectedTeacherContent = !$scope.selectedTeacherContent;
        }


    }]);


}());