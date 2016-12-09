/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';
    angular.module('ecControllers').controller("LibraryCtrl", ['$scope', 'ContentItems', '$routeParams', 'Lessons', 'toaster', '_', 'SharedData', "Search", '$window', '$location', 'APP_EVENTS', 'Tags', 'Utils', '$rootScope',
        function ($scope, ContentItems, $routeParams, Lessons, toaster, _, SharedData, Search, $window, $location, APP_EVENTS, Tags, Utils, $rootScope) {
            var query = {}, performReload = false;
            $scope.$routeParams = $routeParams;
            $scope.lesson = null;
            $scope.selectedLesson = null;
            $scope.lessons = null;
            $scope.lesson_contents = [];
            $scope.isUploaded = false;
            $scope.showSelectLesson = false;
            $scope.filters = [];
            $scope.tags = [];
            $scope.selected_category_id = 0;
            //Strings below are used in the filter but not called by name so initialising here
            var categoryDisplay = gettext("Category");
            var searchDisplay = gettext("Search");
            var tagDisplay = gettext("Tag");

            switch (typeof $routeParams.uploaded) {
                case 'string':
                    $scope.isUploaded = $routeParams.uploaded.toLowerCase() === "true";
                    break;
                case 'boolean':
                    $scope.isUploaded = $routeParams.uploaded;
                    break;
                default:
                    $scope.isUploaded = false; //Preloaded is the default
            }

            $scope.init = function () {
                getUploaded();
                getPreloaded();
                getTags();
            };

            var getLessonsForSelect = function () {
                Lessons.get({ 'page_size': 1000 }, function (response) {
                    $scope.lessons = response.results;
                });
            };

            var replaceFilter = function (type, filter) {
                $scope.filters = _.reject($scope.filters, function (f) { return f.type == type; });
                if (filter) {
                    filter.displayType = gettext(filter.type);
                    $scope.filters.push(filter);
                }
                var params = $location.search();
                var performURLUpdate = false;
                switch (type) {
                    case 'all':
                        query.c = params.c = query.t = params.t = query.search = params.search = null;
                        $scope.filters = [];
                        performURLUpdate = true;
                    case 'Category':
                        var val = filter ? filter.id : null;
                        if (params.c != val)
                            performURLUpdate = true;
                        query.c = params.c = val;
                        break;
                    case 'Tag':
                        var val = filter ? filter.id : null;
                        if (params.t != val)
                            performURLUpdate = true;
                        query.t = params.t = val;
                        break;
                    case 'Search':
                        var val = filter ? filter.text : null;
                        if (params.search != val)
                            performURLUpdate = true;
                        query.search = val;
                        if (query.search == null)
                            delete params.search;
                        break;
                }

                if (performURLUpdate) {
                    Utils.executeFn(function () {
                        var path = $location.path();
                        if (path.indexOf('library') > -1)
                            $location.search(params);
                        else
                            $location.path('/library').search(params);
                    });
                }
                return performURLUpdate;
            };

            if ($routeParams.lesson && isNaN($routeParams.lesson) == false) {
                Lessons.get({ id: $routeParams.lesson }, function (response) {
                    $scope.lesson = response;
                    $scope.lesson_contents = response.members;
                });
            }

            if ($routeParams.upage && isNaN($routeParams.upage) == false) {
                query.upage = $routeParams.upage;
            }

            if ($routeParams.ppage && isNaN($routeParams.ppage) == false) {
                query.ppage = $routeParams.ppage;
            }

            if ($routeParams.c && isNaN($routeParams.c) == false) {
                $scope.selected_category_id = query.c = $routeParams.c;
            } else {
                query.c = null;
            }

            if ($routeParams.t && isNaN($routeParams.t) == false) {
                query.t = $routeParams.t;
            }

            query.ordering = $routeParams.ordering;

            if ($routeParams.search) {
                replaceFilter('Search', { type: 'Search', text: $routeParams.search });
            } else {
                //query.page = null;
                replaceFilter('Search');
            }

            $scope.$watch('$routeParams.search', function () {
                if (performReload) {

                    if ($routeParams.search) {
                        replaceFilter('Search', { type: 'Search', text: $routeParams.search });
                    } else {
                        query.page = null;
                        replaceFilter('Search');
                    }

                    Utils.executeFn(function () {
                        getUploaded();
                        getPreloaded();
                        getTags();
                    });
                }
            });

            var getUploaded = function (q) {
                //clear checked items when changing pages
                $rootScope.$broadcast(APP_EVENTS.clearCheckedItems);
                if ($scope.user.isTeacher()) {
                    performReload = false;
                    q = q || angular.copy(query || {});

                    if (q.upage) {
                        q.page = q.upage;
                        q.upage = null;
                    }
                    q.uploaded = "True";
                    ContentItems.get(q, function (data) {
                        $scope.uploaded_items = data;
                        performReload = true;
                        $scope.checkedItems = SharedData.checkedContentItems = [];
                    });
                }
            };

            var getPreloaded = function (q) {
                //clear checked items when changing pages
                $rootScope.$broadcast(APP_EVENTS.clearCheckedItems);
                q = q || angular.copy(query || {});
                performReload = false;
                if (q.ppage) {
                    q.page = q.ppage;
                    q.ppage = null;
                }
                if ($scope.user.isTeacher()) {
                    q.uploaded = "False";
                    q.hidden = null;
                } else {
                    $scope.isUploaded = false;
                    q.uploaded = null;
                    q.hidden = "False";
                }

                ContentItems.get(q, function (data) {
                    $scope.preloaded_items = data;
                    performReload = true;
                    $scope.checkedItems = SharedData.checkedContentItems = [];
                });
            };

            var getTags = function (q) {
                q = q || angular.copy(query || {});
                q.ordering = '-uses';

                Tags.query(q, function (data) {
                    $scope.tags = data.results;
                    if ($routeParams.t && isNaN($routeParams.t) == false) {
                        var existing = _.find($scope.tags, function (tag) { return tag.id == $routeParams.t; });
                        if (existing)
                            replaceFilter('Tag', { id: existing.id, text: existing.text, type: 'Tag' });
                        else {
                            Tags.get({ id: $routeParams.t }, function (response) {
                                replaceFilter('Tag', { id: response.id, text: response.text, type: 'Tag' });
                            });
                        }
                    }
                }).$promise;
            };

            $scope.showAddToLesson = function () {
                if (!$scope.checkedItems || $scope.checkedItems.length === 0)
                    return;

                $scope.showSelectLesson = true;
                if($scope.lessons == null){
                    getLessonsForSelect();
                }
            };

            $scope.hideAddToLesson = function () {
                $scope.showSelectLesson = false;
            };

            $scope.sortby = function (key) {
                if (query.ordering == key) {
                    key = '-' + key;
                }

                query.ordering = key;
                var params = $location.search();
                params.ordering = key;

                $location.search(params);
                Utils.executeFn(function () {
                    if ($scope.isUploaded)
                        getUploaded();
                    else
                        getPreloaded();
                });
            }

            $scope.page = function (pageNum) {
                var q = angular.copy(query || {});
                var params = $location.search();
                var pageKey = $scope.isUploaded ? "upage" : "ppage";

                q.page = params[pageKey] = pageNum;

                if (q[pageKey])
                    q[pageKey] = null;

                $location.search(params);

                Utils.executeFn(function () {
                    if ($scope.isUploaded)
                        getUploaded(q);
                    else
                        getPreloaded(q);
                });
            }

            $scope.$on(APP_EVENTS.checkedItemsChanged, function () {
                $scope.checkedItems = SharedData.checkedContentItems;
            });

            $scope.batchAdd = function (selectedLesson) {
                $scope.checkedItems = SharedData.checkedContentItems;

                if ($scope.checkedItems.length) {
                    if (!$scope.lesson && !selectedLesson) {
                        toaster.pop('warning', gettext("No Lesson selected"));
                        return;
                    }

                    var doGet = false;
                    if ($scope.lesson) {
                        if (selectedLesson && $scope.lesson.id !== selectedLesson.id)
                            doGet = true;
                    } else {
                        doGet = true;
                    }

                    if (doGet) {
                        Lessons.get({ id: selectedLesson.id }, function (response) {
                            $scope.lesson = response;
                            $scope.lesson_contents = response.members;
                            updateLessonItems();
                        });
                    } else {
                        updateLessonItems();
                    }
                } else {
                    toaster.pop('warning', gettext("No items selected"));
                }
            };

            var updateLessonItems = function () {
                var newItemsCount = 0;
                angular.forEach($scope.checkedItems, function (item) {
                    var existing = _.find($scope.lesson.members, function (member) { return typeof member === 'object' ? member.id === item.id : member === item.id; });
                    if (!existing) {
                        this.push(item);
                        newItemsCount++;
                    }
                }, $scope.lesson.members);

                if (newItemsCount) {
                    Lessons.update($scope.lesson, function (update_response) {
                        Lessons.get({ id: update_response.id }, function (response) {
                            var transmessage = interpolate(gettext("Added to %(lessontitle)s"), { lessontitle: $scope.lesson.title }, true);
                            toaster.pop('success', transmessage);
                            $scope.lesson = response;
                            $scope.lesson_contents = response.members;
                        });
                    });
                } else {
                    toaster.pop('warning', gettext("Items already in list"));
                }
            };

            $scope.batchDelete = function () {
                $scope.checkedItems = SharedData.checkedContentItems;
                if ($scope.checkedItems.length) {
                    var del = $window.confirm(gettext("Are you sure you want to delete?"));
                    if (del) {
                        var ids = [];
                        for (var i = 0, len = $scope.checkedItems.length; i < len; i++) {
                            ids.push($scope.checkedItems[i].id);
                        }

                        $scope.uploadedPromise = ContentItems.bulkdelete({ 'ids': ids }, function () {
                            toaster.pop('success', gettext("Items deleted"));
                            SharedData.clear();
                            getUploaded();
                        });
                    }
                } else {
                    toaster.pop('warning', gettext("No items selected"));
                }
            };

            $scope.addToLesson = function (item) {

                if (!$scope.lesson) {
                    toaster.pop('warning', gettext("No Lesson selected"));
                    return;
                }

                var existing = _.find($scope.lesson.members, function (lessonitem) { return lessonitem.id == item.id });
                if (!existing) {
                    $scope.lesson.members.push(item);
                    Lessons.update($scope.lesson, function (response) {
                        var transmessage = interpolate(gettext("Added to %(lessontitle)s"), { lessontitle: $scope.lesson.title }, true);
                        toaster.pop('success', transmessage);
                        if ($scope.lessons != null) {
                            //Push the item into the corresponding list of content for the lesson in the list of lessons for the dropdown
                            for (var i = 0, len = $scope.lessons.length; i < len; i++) {
                                if ($scope.lessons[i].id === $scope.lesson.id) {
                                    $scope.lessons[i].members.push(item);
                                    break;
                                }
                            }
                        }
                    });
                } else {
                    toaster.pop('warning', gettext("Item already in list"));
                }
            };

            $scope.switchview = function (view) {
                //clear checked items when changing tabs
                $scope.checkedItems = [];
                $rootScope.$broadcast(APP_EVENTS.clearCheckedItems);

                if ((view === 'uploaded' && !$scope.isUploaded) || (view === 'preloaded' && $scope.isUploaded)) {
                    $scope.isUploaded = !$scope.isUploaded;
                }
                var params = $location.search();
                if ($scope.isUploaded)
                    params.uploaded = true;
                else
                    params.uploaded = null;

                $location.search(params);
            };

            $scope.tagFilter = function (tag, e) {
                e.preventDefault();
                e.stopPropagation();
                replaceFilter('Tag', { type: 'Tag', text: tag.text, id: tag.id });
                Utils.executeFn(function () {
                    getUploaded();
                    getPreloaded();
                });
            };

            $scope.categoryFilter = function (selectedCategory) {
                var reload = replaceFilter('Category', { type: 'Category', text: selectedCategory.text, id: selectedCategory.id });
                if (reload) {
                    Utils.executeFn(function () {
                        getUploaded();
                        getPreloaded();
                        getTags();
                    });
                }
            };

            $scope.clearFilter = function (type) {
                replaceFilter(type);
                if (type == 'Category')
                    $('.jstree').jstree("deselect_all", true);
                Utils.executeFn(function () {
                    getUploaded();
                    getPreloaded();
                    getTags();
                });

            };

            $scope.resultsMessage = function (resCount) {
                if (resCount)
                    return '';

                if ($routeParams.search || $routeParams.t || $routeParams.c)
                    return gettext("No results returned.");

                return ''
            };

        }]);
}());