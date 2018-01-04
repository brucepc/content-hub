/// <reference path="../../angularjs/angular.js" />
(function () {
   
    angular.module('ecFilters', []).filter('filesizeformat', function () {
        return function (bytes, precision) {
            if (bytes === 0) { return '0 B' }
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;

            var units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024)),
                val = (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision);

            return (val.match(/\.0*$/) ? val.substr(0, val.indexOf('.')) : val) + ' ' + units[number];
        }
    }).filter('get_filename', function () {
        return function (path) {
            if (!path) return '';
            return path.replace(/^.*[\\\/]/, '')
        }
    }).filter('get_extension', function () {
        return function (path) {
            if (!path)
                return '';

            var CSS_ICON_TYPES = ["ai", "apk", "avi", "bmp", "css", "dir", "dll", "dmg", "doc", "docx", "eps", "exe", "fla", "gif", "gz", "gzip", "html", "indd", "iso", "jpeg", "jpg", "js", "midi", "mov", "mp3", "mp4", "mpeg", "otf", "pdf", "php", "png", "ppt", "pptx", "psd", "pub", "rar", "rtf", "svg", "swf", "tar", "tiff", "txt", "url", "wav", "wma", "xls", "xlsx", "xml", "zip"];
            var file_extension = path.toLowerCase().split('.').pop();

            if (CSS_ICON_TYPES.indexOf(file_extension) > -1)
                // This extension is on the list of css classes, so just pass it straight through
                return file_extension;
            else
                //Check if this extension needs to be translated, if not just use 'generic'
                //return FILE_TYPE_TRANSLATIONS.get(file_extension, 'generic')
                return 'generic';
        }
    
    }).filter('encode_params', function () {
        return function (params, toStrip) {
            var parts = [];
            angular.forEach(params, function (value, key) {
                if (key.toLowerCase() !== toStrip) {
                    parts.push(key + (value === true ? '' : '=' + value));
                }
            });
            return parts.length ? '&' + parts.join('&') : '';
        }

    }).filter('build_url', function () {
        return function (base, params) {
            var parts = [];
            angular.forEach(params, function (value, key) {
                parts.push(key + (value === true ? '' : '=' + value));
            });
            
            if (base.indexOf('?') > -1)
                return base + '&' + parts.length ? parts.join('&') : '';

            return base + '?' + parts.length ? parts.join('&') : '';
        }

    }).filter('range', function () {
        return function (input, total) {
            total = parseInt(total);
            for (var i = 0; i < total; i++)
                input.push(i);
            return input;
        };
    }).filter('array_display', function () {
        return function (array, key) {
            if (array) {
                if(key)
                    return array.map(function (elem) { return elem[key]; }).join(', ');

                return array.join(', ');
            }
            return '';
        }

    });

}());