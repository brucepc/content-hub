/// <reference path="../../angularjs/angular.js" />
(function () {
    "use strict"

    angular.module("updateDirectives", []).directive('match', function () {
        return {
            require: 'ngModel',
            restrict: 'A',
            scope: {
                match: '='
            },
            link: function (scope, elem, attrs, ctrl) {
                scope.$watch(function () {
                    return (ctrl.$pristine && angular.isUndefined(ctrl.$modelValue)) || scope.match === ctrl.$modelValue;
                }, function (currentValue) {
                    ctrl.$setValidity('match', currentValue);
                });
            }
        };
    });
}());