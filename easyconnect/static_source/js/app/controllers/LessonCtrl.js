/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    angular.module('ecControllers').controller("LessonCtrl", ['$scope', 'Lessons', '$routeParams', 'toaster', "Search", '$location', '_', 'SharedData', '$window', '$q', 'APP_EVENTS', 'FIELD_VAL', 'Utils',
    function ($scope, Lessons, $routeParams, toaster, Search, $location, _, SharedData, $window, $q, APP_EVENTS, FIELD_VAL, Utils) {
        var query = {};
        $scope.$location = $location;
        $scope.FIELD_VAL = FIELD_VAL;
        $scope.checkedLessons = [];
        $scope.checkedItems = [];
        $scope.breadcrumbs = {};
        var validationLessons = [];

        var getLessonsForValidation = function () {
            if ($scope.user.isTeacher()) { //Only a teacher will need a list of lessons
                Lessons.get({ 'page_size': 1000 }, function (response) {
                    validationLessons = response.results;
                });
            }
        };

        $scope.init = function (param) {
            query = param || query;
            refreshlist();
            getLessonsForValidation();
        };

        if ($routeParams.Id) {
            Lessons.get({ id: $routeParams.Id }, function (response) {
                $scope.lesson = response;
            });
            getLessonsForValidation();
        }

        if ($routeParams.page) {
            query = query || {};
            query.page = $routeParams.page;
        }

        query.ordering = $routeParams.ordering;

        var refreshlist = function () {
            $scope.checkedLessons = [];
            $scope.lessonsPromise = Lessons.get(query, function (data) {
                $scope.lessons = data;
            }).$promise;
        };

        if ($routeParams.search) {
            query.search = $scope.breadcrumbs.search = $routeParams.search;
        } else {
            $scope.breadcrumbs.search = null;
            query.search = null;
        }

        $scope.sortby = function (key) {
            if (query.ordering == key) {
                if (key.indexOf('-') === 0)
                    key = key.replace('-', '');
                else
                    key = '-' + key;
            }

            query.ordering = key;
            var params = $location.search();
            params.ordering = key;
            $location.search(params);
            refreshlist();
        };

        var currentItemSort = null;
        $scope.sortItems = function (key) {
            $scope.lesson.members = _.sortBy($scope.lesson.members, function (item) { return item[key]; });

            if (currentItemSort === key) {
                $scope.lesson.members.reverse();
                currentItemSort = null;
            } else {
                currentItemSort = key;
            }
        };

        $scope.page = function (pageNum) {
            query = query || {};
            query.page = pageNum
            refreshlist();
        };

        $scope.featuretoggle = function (event, lesson) {
            event.stopPropagation();
            if ($scope.working)
                return;

            $scope.working = true;
            lesson.featured = !lesson.featured;
            $scope.lessonsPromise = Lessons.update(lesson, function () {
                if (query) refreshlist();
                toaster.pop('success', lesson.featured ? gettext("Featured") : gettext("Unfeatured"));
            }).$promise.then(function () { $scope.working = false; });

        };

        $scope.checkedtoggle = function (lesson) {
            if ($location.path() == '/') //prevent lesson from being selected on home page
                return;

            var found = false;
            for (var i = 0, len = $scope.checkedLessons.length; i < len; i++) {
                if (lesson.id === $scope.checkedLessons[i].id) {
                    $scope.checkedLessons.splice(i, 1);
                    found = true;
                    break;
                }
            }
            if (!found) $scope.checkedLessons.push(lesson);
        };

        var resetQueryString = function () {
            var params = $location.search();
            if (params && params.createlesson && validationLessons.length === 0) {
                Utils.executeFn(function () {
                    params.createlesson = null;
                    $location.search(params);
                });
            }
        }

        $scope.toggleForm = function (show) {
            $scope.showForm = show;
            $scope.newLesson = '';
            if (!show)
                resetQueryString();
        };


        if ($routeParams.createlesson) {
            $scope.toggleForm(true);
        }

        $scope.addLesson = function (title, form) {
            var valresult = $scope.validate({ id: 0 }, title);
            if (typeof valresult === 'undefined') {
                form.title.$setValidity('custom', true);

                var newLesson = new Lessons({ 'title': sanitize(title) });
                newLesson.$save(function (success) {
                    toaster.pop('success', gettext("Lesson added"));
                    validationLessons.push(success);
                    $scope.toggleForm(false);
                    refreshlist();
                });
            } else {
                form.title.$setValidity('custom', false);
                $scope.customError = valresult;
            }
        };

        $scope.validate = function (lesson, title) {
            if (!title)
                return gettext("This is a required field");

            title = sanitize(title).toUpperCase();

            if (title.length > FIELD_VAL.lessonMax) {
                return interpolate(gettext("The maximum length of title is %(max)s"), { max: FIELD_VAL.lessonMax }, true);
            }
            console.log(validationLessons);
            console.log(title);
            var existing = _.find(validationLessons, function (les) { return les.title.toUpperCase() === title && les.id !== lesson.id; });
            console.log(existing);
            console.log('-----');
            if (existing)
                return gettext("Duplicate");

        };

        $scope.update = function (lesson, form) {
            if (lesson.title) {
                lesson.title = sanitize(lesson.title);
                $scope.lessonsPromise = Lessons.update(lesson, function (updatedLesson) {
                    _.find(validationLessons, function (les) {
                        if (les.id == updatedLesson.id) {
                            les.title = updatedLesson.title;
                        }
                    });
                    toaster.pop('success', gettext("Title Updated"));
                }).$promise;
            }
        };

        $scope.remove = function (lesson) {
            var del = $window.confirm(gettext("Are you sure you want to delete?"));
            if (del) {
                $scope.lessonsPromise = Lessons.remove({ id: lesson.id }, function (response) {
                    validationLessons = _.reject(validationLessons, function (les) { return les.id === lesson.id; });
                    toaster.pop('success', gettext("Lesson Deleted"));
                    $location.path($routeParams.next || '/lessons');
                }).$promise;
            }
        };

        $scope.removeItems = function () {
            if ($scope.checkedItems && $scope.checkedItems.length) {
                var del = $window.confirm(gettext("Remove from Lesson?"));
                if (del) {
                    $scope.lesson.members = _.reject($scope.lesson.members, function (item) { return _.find($scope.checkedItems, function (checked) { return item.id === checked.id; }) != null });
                    $scope.checkedItems = [];
                    $scope.lessonsPromise = Lessons.update($scope.lesson, function (response) {
                        toaster.pop('success', gettext("Items Removed"));
                        $scope.checkedItems = SharedData.checkedContentItems = [];
                    }).$promise;
                }
            }
        };

        $scope.batchDelete = function () {

            if ($scope.checkedLessons.length) {
                var del = $window.confirm(gettext("Are you sure you want to delete?"));
                if (del) {
                    var promises = [];
                    for (var i = 0, len = $scope.checkedLessons.length; i < len; i++) {
                        promises.push(Lessons.remove({ id: $scope.checkedLessons[i].id }).$promise);
                        validationLessons = _.reject(validationLessons, function (les) { return les.id === $scope.checkedLessons[i].id; });
                    }
                    $q.all(promises).then(function () {
                        toaster.pop('success', gettext("Lesson Deleted"));
                        refreshlist();
                        resetQueryString();
                    });
                }
            }
        };

        $scope.$on(APP_EVENTS.checkedItemsChanged, function () {
            $scope.checkedItems = SharedData.checkedContentItems;
        });

        var sanitize = function (text) {
            if (!text)
                return '';

            return text.replace(/^\s+|\s+$/gm, '');
        };
    }
    ]);
}());