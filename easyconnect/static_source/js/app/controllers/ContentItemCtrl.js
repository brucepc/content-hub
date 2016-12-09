/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //* ContentItem controller for content item functionality in the Home page, library, Item Edit, and lesson details page
    ////////////////////////////////////////
    angular.module('ecControllers').controller("ContentItemCtrl", ["$scope", "ContentItems", '$routeParams', '$location', 'Lessons', 'toaster', '_', 'SharedData', 'Categories', '$rootScope', '$window', 'APP_EVENTS', 'Utils',
    function ($scope, ContentItems, $routeParams, $location, Lessons, toaster, _, SharedData, Categories, $rootScope, $window, APP_EVENTS, Utils) {
        var query = {};
        $scope.$location = $location;
        $scope.checkedItems = [];
        $scope.working = false;
        $scope.editing = false;
        $scope.content_file = { dummy: 'data for validation' };
        $scope.embedded = true;
        $scope.inLessons = $location.path().indexOf("lessons") > -1;
        $scope.content = {};
        $scope.selected_category_id = 0;
        
        $scope.$on('$destroy', function () {
            $(window).off('beforeunload');
        });
        $(window).on('beforeunload', function (e) {
            if ($scope.uploadForm) {
                if ($scope.uploadForm.$dirty) {
                    var message = gettext('If you leave this page all unsaved changes will be lost, are you sure?');
                    e.returnValue = message;
                    return message;
                }
            }
        });
        $scope.$on('$locationChangeStart', function (event) {
            if ($scope.uploadForm) {
                if (!$scope.uploadForm.$dirty) return;
                var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                if (!answer) {
                    event.preventDefault();
                }
            }
        });

        $scope.selectCategory = function (selectedCategory) {
            $scope.category = selectedCategory
            $scope.uploadForm.$setDirty();
            $scope.$apply();
        };

        $scope.clearCategory = function () {
            $scope.category = null;
            $scope.uploadForm.$setDirty();
            $scope.$apply();
        };

        if ($routeParams.id && !$scope.inLessons) {
            $scope.editing = true;
            ContentItems.get({ id: $routeParams.id }, function (response) {
                $scope.content = response;
                if (response.categories && response.categories.length) {
                    $scope.selected_category_id = response.categories[0].id;
                    $scope.category = response.categories[0];
                }
            });
        }

        if ($routeParams.page) {
            query.page = $routeParams.page;
        }

        $scope.init = function (param, embedded) {
            $scope.embedded = typeof embedded === 'undefined' ? true : embedded;
            query = param;
            refreshlist();
        };

        $scope.page = function (pageNum) {
            query = query || {};
            query.page = pageNum
            refreshlist();
        }

        var refreshlist = function () {
            if (!$scope.embedded) {
                $scope.contentItemsPromise = ContentItems.get(query, function (data) {
                    $scope.contentitems = data;
                }).$promise;
            }
        };

        $scope.$on(APP_EVENTS.featuredContentChanged, function () {
            refreshlist();
        });

        $scope.remove = function (item) {
            var del = $window.confirm(gettext("Are you sure you want to delete?"));
            if (del) {
                $scope.contentItemsPromise = ContentItems.remove({ id: item.id }, function (response) {
                    toaster.pop('success', gettext("Item deleted"));
                    $scope.checkedtoggle(item);
                    refreshlist();
                }).$promise;
            }
        };

        $scope.save = function (contentItem, form) {
            $scope.working = true;
            if (form.$valid) {
                contentItem.categories = [];
                if ($scope.category && $scope.category != '-1') {
                    contentItem.categories.push($scope.category);
                }
                ContentItems.update(contentItem, function (success) {
                    $scope.working = false;
                    toaster.pop('success', gettext("Item successfully updated"));
                    $scope.$destroy(); //call destroy to unbind the dirty bit
                    var redirectTo = Utils.createLibraryRedirect($routeParams);
                    $scope.$location.url(redirectTo);
                });
            }
        };

        $scope.addToLesson = function (item) {
            var existing = _.find($scope.lesson.members, function (lessonitem) { return lessonitem.id == item.id });
            if (!existing) {
                $scope.lesson.members.push(item);
                Lessons.update($scope.lesson, function (response) {
                    toaster.pop('success', interpolate(gettext("Added to %(lesson)s"), { lesson: $scope.lesson.title }, true));
                });
            } else {
                toaster.pop('warning', gettext("Item already in list"));
            }
        };

    }
    ]);
}());