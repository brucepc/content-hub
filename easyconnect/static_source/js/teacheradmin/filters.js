/// <reference path="../../angularjs/angular.js" />
(function () {
    'use strict';

    angular.module('taFilters', []).filter('get_filename', function () {
        return function (path) {
            if (!path) return '';
            return path.replace(/^.*[\\\/]/, '')
        }
    }).filter('filesizeformat', function () {
        return function (bytes, precision) {
            if (bytes === 0) { return '0 B' }
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;

            var units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024)),
                val = (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision);

            return (val.match(/\.0*$/) ? val.substr(0, val.indexOf('.')) : val) + ' ' + units[number];
        }
    });

}());