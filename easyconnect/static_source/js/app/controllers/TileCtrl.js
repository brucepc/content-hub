/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    //angular.module('ecControllers').controller("TileCtrl", ["$scope", "$rootScope", 'toaster', "Tiles", '$window', 'APP_EVENTS', 'SharedData', '$routeParams', 'FIELD_VAL', '$location', 'Utils',
    //function ($scope, $rootScope, toaster, Tiles, $window, APP_EVENTS, SharedData, $routeParams, FIELD_VAL, $location, Utils) {

    //    $scope.tiles = [];
    //    var query = {};
    //    $scope.$location = $location;
    //    $scope.FIELD_VAL = FIELD_VAL;

    //    var refreshlist = function () {
    //        $scope.tiles = [];
    //        //if ($scope.user.is_authenticated) {
    //        Tiles.query(function (response) {
    //            if (response.results){
    //                $scope.tiles = response.results;
    //            }
    //        });
    //        //}
    //    };
    //    refreshlist();

    //    var resetQueryString = function () {
    //        var params = $location.search();
    //        if (params && params.createtile /*&& validationLessons.length === 0*/) {
    //            Utils.executeFn(function () {
    //                params.createtile = null;
    //                $location.search(params);
    //            });
    //        }
    //    }

    //    $scope.toggleForm = function (show) {
    //        $scope.showForm = show;
    //        $scope.newTile = {};
    //        if (!show)
    //            resetQueryString();
    //    };

    //    if ($routeParams.createtile) {
    //        $scope.toggleForm(true);
    //    }

    //    $scope.addTile = function (model, form) {
    //        var valresult = $scope.validate({ id: 0 }, model.title);
    //        if (typeof valresult === 'undefined') {
    //            form.title.$setValidity('custom', true);

    //            var newTile = new Tiles({
    //                'title': model.title,
    //                'url': model.url,
    //                'icon': model.icon
    //            });
    //            newTile.$save(function (success) {
    //                toaster.pop('success', gettext("Tile added"));
    //                //validationLessons.push(success);
    //                $scope.toggleForm(false);
    //                refreshlist();
    //            });
    //        } else {
    //            form.title.$setValidity('custom', false);
    //            $scope.customError = valresult;
    //        }
    //    };

    //    $scope.validate = function (lesson, title) {
    //        if (!title)
    //            return gettext("This is a required field");

    //        //title = sanitize(title).toUpperCase();

    //        if (title.length > FIELD_VAL.tilenameMax) {
    //            return interpolate(gettext("The maximum length of title is %(max)s"), { max: FIELD_VAL.tilenameMax }, true);
    //        }
    //        /*
    //        console.log(validationLessons);
    //        console.log(title);
    //        var existing = _.find(validationLessons, function (les) { return les.title.toUpperCase() === title && les.id !== lesson.id; });
    //        console.log(existing);
    //        console.log('-----');
    //        if (existing)
    //            return gettext("Duplicate");
    //        */
    //    };


    //}]);


}());