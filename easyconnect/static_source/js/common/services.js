/// <reference path="../../angularjs/angular.js" />
(function () {
    'use strict';

    //Versions of IE before IE9 don't have an .indexOf() function for Array. Code blow is Firefox's implementation
    if (!Array.prototype.indexOf) { Array.prototype.indexOf = function (e) { var t = this.length >>> 0; var n = Number(arguments[1]) || 0; n = n < 0 ? Math.ceil(n) : Math.floor(n); if (n < 0) n += t; for (; n < t; n++) { if (n in this && this[n] === e) return n } return -1 } }

    //Polyfill for browsers that don't support map() 
    // Production steps of ECMA-262, Edition 5, 15.4.4.19
    // Reference: http://es5.github.io/#x15.4.4.19
    if (!Array.prototype.map) { Array.prototype.map = function (e, t) { var n, r, i; if (this == null) { throw new TypeError(" this is null or not defined") } var s = Object(this); var o = s.length >>> 0; if (typeof e !== "function") { throw new TypeError(e + " is not a function") } if (arguments.length > 1) { n = t } r = new Array(o); i = 0; while (i < o) { var u, a; if (i in s) { u = s[i]; a = e.call(n, u, i, s); r[i] = a } i++ } return r } }

    navigator.sayswho = (function () {
        var ua = navigator.userAgent, tem,
        M = ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
        if (/trident/i.test(M[1])) {
            tem = /\brv[ :]+(\d+)/g.exec(ua) || [];
            return 'IE ' + (tem[1] || '');
        }
        if (M[1] === 'Chrome') {
            tem = ua.match(/\bOPR\/(\d+)/)
            if (tem != null) return 'Opera ' + tem[1];
        }
        M = M[2] ? [M[1], M[2]] : [navigator.appName, navigator.appVersion, '-?'];
        if ((tem = ua.match(/version\/(\d+)/i)) != null) M.splice(1, 1, tem[1]);
        return M.join(' ');
    })();

    var objToIdArray = function (array) {
        var tmp = [];
        if (array && array.length > 0) {
            for (var i = 0, len = array.length; i < len; i++) {
                tmp.push(typeof array[i] === 'object' ? array[i].id : array[i]);
            }    
        }
        return tmp;
    };

    var transformJsonForContent = function (origData, headersGetter, asObject) {
        var data = angular.copy(origData);
        asObject = asObject || false;

        data.tags = objToIdArray(data.tags);
        data.categories = objToIdArray(data.categories);

        if (!asObject) {
            return angular.toJson(data);
        }
        else {
            return data;
        }
    };

    var transformJsonForContentBasic = function (origData, headersGetter, asObject) {
        var data = angular.copy(origData);
        asObject = asObject || false;
        if (!asObject) {
            return angular.toJson(data);
        }
        else {
            return data;
        }
    };

    angular.module("ecServices", ['ngResource'])
    .factory('Search', function ($resource) {
        return $resource("/rest/search/:type/?", {},
        {
            lessons: { method: 'POST', params: { type: 'lessons' }, isArray: true },
            contentItems: { method: 'POST', params: { type: 'contentitems' }, isArray: true }
        });
    }).factory('Lessons', function ($resource) {
        return $resource("/rest/lessons/:id/?", {}, {
            update: {
                method: 'PUT', params: { id: '@id' }, transformRequest: function (origData) {
                    var data = angular.copy(origData);
                    data.members = objToIdArray(data.members);

                    return angular.toJson(data);
                }
            },
            query: { method: 'GET', isArray: false },
            save: { method: 'POST', url: "/rest/lessons/?" }

        });
    }).factory('ContentItems', function ($resource) {

        return $resource("/rest/contentitems/:id/?", {}, {
            save: {
                method: 'POST',
                url: "/rest/contentitems/?",
                transformRequest: function (form) {
                    var formData = new FormData();
                    var tagsField = 'tags', category3Field = 'category3', category2Field = 'category2', category1Field = 'category1';
                    if (form.metadata[tagsField] && form.metadata[tagsField].length > 0) {
                        for (var i = 0, len = form.metadata[tagsField].length; i < len; i++) {
                            formData.append(tagsField, form.metadata[tagsField][i].id);
                        }
                    }

                    //add form field metadata
                    for (var field in form.metadata) {
                        if (field == tagsField || field == category1Field || field == category2Field || field == category3Field) {
                            continue;
                        } else {
                            formData.append(field, form.metadata[field]);
                        }
                    }

                    //add file
                    formData.append("content_file", form.file);

                    return formData;
                }, headers: { 'Content-Type': undefined }
            },
            update: {
                method: 'PUT', params: { id: '@id' }, transformRequest: transformJsonForContent
            },
            query: { method: 'GET', isArray: false, url: "/rest/contentitems/?" },
            bulkdelete: { method: 'POST', url: '/rest/bulkdelete/?' } //data format = {“ids”: [1, 2, 3, 4 … n-1, n]}

        });
    }).factory('Tags', function ($resource) {
        return $resource("/rest/tags/:id/?", {}, {
            query: { method: 'GET', isArray: false },
            update: { method: 'PUT', params: { id: '@id' } }
        });
    }).factory('Categories', function ($resource) {
        return $resource("/rest/categories/:id/?", {}, {
            update: { method: 'PUT', params: { id: '@id' } }
        });
    }).factory('Categorytree', function ($resource) {
        return $resource("/rest/categorytree/?", {});
    }).factory('Settings', function ($resource) {

        return $resource("/rest/settings/:setting/?", {}, {
            checkInternet: {
                method: 'GET', params: { 'setting': 'internet' }
            },
            checkLibrary: {
                method: 'GET', params: { 'setting': 'library' }
            },
            getSSID: {
                method: 'GET', params: { 'setting': 'ssid' }
            },
            toggleInternet: {
                method: 'POST', params: { 'setting': 'internet' }
            },
            toggleLibrary: {
                method: 'POST', params: { 'setting': 'library' }
            },
            toggleViewType: {
                method: 'POST', params: { 'setting': 'toggleviewtype', 'type': '@type' }
            },
            setSSID: {
                method: 'POST', params: { 'setting': 'ssid', 'ssid': '@ssid' }
            },
            updatePassword: {
                method: 'POST', params: { 'setting': 'changepassword' }
            },
            resetTeacherAccount: {
                method: 'POST', params: { 'setting': 'resetteacheraccount' }
            },
            checkRemoteManagement: {
                method: 'GET', params: { 'setting': 'remotemanagement' }
            },
            checkStudy: {
                method: 'GET', params: { 'setting': 'study' }
            },
            toggleRemoteManagement: {
                method: 'POST', params: { 'setting': 'remotemanagement', 'remotemanagement': '@remotemanagement' }
            },
            toggleStudy: {
                method: 'POST', params: { 'setting': 'study' }
            },
            getCAPVersion: {
                method: 'GET', params: { 'setting': 'capversion' }
            }
        });
    }).factory('_', function () {
        return window._; // assumes underscore has already been loaded on the page
    }).factory('SharedData', ['$rootScope', 'APP_EVENTS', function ($rootScope, APP_EVENTS) {
        var checkedContentItems = [];
        return {
            checkedContentItems: checkedContentItems,
            clear: function () { $rootScope.$broadcast(APP_EVENTS.clearCheckedItems); }
        };
    }]).factory('USB', function ($resource) {
        return $resource("/rest/usb_util/upload/?", {}, {
            listDrives: {
                method: 'GET',
                isArray: true
            },
            uploadContent: {
                method: 'POST', transformRequest: transformJsonForContent
            }
        });
    }).factory("USB2", function ($resource, $q, $http) {
        var cancellable_method = function (form) {
            var canceller = $q.defer();
            var cancel = function (reason) {
                canceller.resolve(reason);
            };
            var promise = $http.post('/rest/usb_util/upload/?', {}, {
                method: 'POST',
                url: '/rest/usb_util/upload/?',
                transformRequest: transformJsonForContent,
                timeout: canceller.promise
            });
            return {
                promise: promise,
                cancel: cancel
            };
        }
        return {
            cancellable_method: cancellable_method
        };
    }).factory("userService", function ($http, $resource, localStorageService, $cookies) {
        var auth_api_url = "/rest/auth/?";
        var tokenauth_api_url = "/rest/tokenauth/?";
        var user = {};
        user.isAdmin = function () { return this.type === 'admin'; }
        user.isTeacher = function () { return this.type === 'teacher'; };

        var auth = $resource(auth_api_url, {},
            {
                login: { method: 'POST' },
                logout: { method: 'DELETE' }
            });

        var token_auth = $resource(tokenauth_api_url, {},
            {
                login: { method: 'GET' }
            });

        var setUser = function (data) {
            if (data) {
                if (data.is_superuser) {
                    user.is_authenticated = true;
                    user.type = "admin";
                    user.username = data.username;
                    user.is_superuser = data.is_superuser;
                }
                else {
                    user.is_authenticated = true;
                    user.type = "teacher";
                    user.username = data.username;
                    user.is_superuser = data.is_superuser;
                }
                localStorageService.set('authType', data.is_superuser);
            } else {
                user.is_authenticated = false;
                user.type = "student";
                user.username = "";
                user.is_superuser = false;
            }
        };



        setUser(null);

        var authFromToken = function () {
            return token_auth.login(function (response) {
                setUser(response);
            });
        };

        var auth_data = localStorageService.get('authorizationData');

        if (null != auth_data) {
            //If a token exists set user to teacher and authenticate to prevent latency waiting for server response
            //If token has expired user will be logged out
            user.is_authenticated = true;
            user.type = "admin";
            var token = localStorageService.get('authorizationData')['token'];
            $http.defaults.headers.common['Authorization'] = 'Token ' + token;
            $cookies['authorizationData'] = token;
            authFromToken();
        }

        return {
            login: function (username, password) {
                return auth.login({ 'username': username, 'password': password }, function (response) {
                    localStorageService.set('authorizationData', { token: response.token });
                    $cookies['authorizationData'] = response.token;
                    $http.defaults.headers.common['Authorization'] = 'Token ' + response.token;
                    authFromToken();//now go back and get user type with token
                    //setUser({ username: "teacher", is_superuser: false });
                });
            },
            get: function () { return user; },
            logout: function () {
                setUser(null);
                $http.defaults.headers.common['Authorization'] = null;//'Basic';
                localStorageService.remove('authorizationData')
                delete $cookies['authorizationData'];
                localStorageService.remove('authType');
            },
            authFromToken: authFromToken
        };
    }).factory("Utils", ['blockUI', '$timeout', function (blockUI, $timeout) {
        return {
            createLibraryRedirect: function (params, defaultUrl) {
                var redirectTo = params.next || defaultUrl || '/library';
                var parts = []
                if (params.c)
                    parts.push('c=' + params.c);

                if (params.t)
                    parts.push('t=' + params.t);

                if (params.search)
                    parts.push('search=' + params.search);

                if (params.uploaded)
                    parts.push('uploaded');

                if (params.upage)
                    parts.push('upage=' + params.upage);

                if (params.ppage)
                    parts.push('ppage=' + params.ppage);

                if (params.ordering)
                    parts.push('ordering=' + params.ordering);

                redirectTo += parts.length ? '?' + parts.join('&') : '';
                return redirectTo;
            },
            executeFn: function (callback, executeNow) {
                if (callback && typeof callback === 'function') {
                    if (blockUI.state().blockCount > 0) {
                        blockUI.done(callback);
                    } else {
                        $timeout(callback, 500);
                    }
                    if (executeNow)
                        blockUI.reset(true);
                }
            }
        };
    }]).factory("ecInterceptor", ['$q', 'toaster', 'localStorageService', '$location', '$rootScope', '$injector', '$window', function ($q, toaster, localStorageService, $location, $rootScope, $injector, $window) {
        var showMessage = function (message, title, time) {
            toaster.pop('error', title, message, false);
        };

        return {
            // optional method
            'request': function (config) {
                // do something on success
                return config;
            },

            // optional method
            'requestError': function (rejection) {
                // do something on error
                return $q.reject(rejection);
            },

            // optional method
            'response': function (response) {
                // do something on success
                return response;
            },

            // optional method
            'responseError': function (errorResponse) {
                switch (errorResponse.status) {
                    case 0:
                    case 404:
                        showMessage(gettext("Please verify your connection and try again. If issue persists contact administrator."), gettext("Connection unavailable."), 0);
                        break;
                    case 400: // if the status is 400 we return the error
                        if ($location.path().indexOf('/login') === -1) {
                            showMessage(errorResponse.data.message, gettext("Bad Request"), 6000);
                            // if we have found validation error messages we will loop through
                            // and display them
                            if (errorResponse.data) {
                                for (var err in errorResponse.data) {
                                    showMessage(errorResponse.data[err],
                                      'Error', 6000);
                                }
                            }
                        }
                        break;
                    case 403: // if the status is 403 we tell the user that authorization was denied
                        //showMessage('You have insufficient privileges to do what you want to do!',
                        //'Authorization Required', 6000);
                        //if user is not authorized, delete token if exists & redirect to login
                        localStorageService.remove('authorizationData');
                        localStorageService.remove('authType');
                        var $http = $injector.get('$http');
                        $http.defaults.headers.common['Authorization'] = 'Basic';
                        $rootScope.$broadcast('token-timeout');
                        //var currentpath = $location.path();
                        $location.path('/');//.search('next', currentpath);
                        $window.location.reload();

                        break;
                    case 409: // if the status is 409 we return conflict with operation being performed
                        showMessage(errorResponse.statusText,
                          errorResponse.status, 6000);
                        break;
                    case 413: //File size too large
                        showMessage(gettext("There is not enough space on the internal drive.  Please connect external drive and retry."), errorResponse.status, 6000);
                        break;
                    case 500: // if the status is 500 we return an internal server error message
                        showMessage(errorResponse.data.message,
                          'Internal server error', 6000);
                        break;
                    default: // for all other errors we display a default error message
                        //if the data object contains a message display that.
                        var userMessage;
                        if (errorResponse.data && errorResponse.data.message)
                            userMessage = errorResponse.data.message;
                        else
                            userMessage = interpolate(gettext("An Error has occurred (%(status)s)"), { status: errorResponse.status }, true);
                        showMessage(gettext("Please try again!"), userMessage, 6000);
                }
                return $q.reject(errorResponse);
            }
        };
    }

    ]).factory("Packages2", function ($resource, $q, $http) {
        var cancellable_method = function (form) {
            var formData = new FormData();
            formData.append("content_file", form.file);
            formData.append("overwrite", true);
            var canceller = $q.defer();
            var cancel = function (reason) {
                canceller.resolve(reason);
            };
            var promise = $http.post("/rest/packages/?", formData, {
                method: 'POST',
                url: '/rest/packages/?',
                transformRequest: angular.identity,
                headers: { 'X-Progress-ID': form.x_progress_id, 'Content-Type': undefined },
                timeout: canceller.promise
            });
            return {
                promise: promise,
                cancel: cancel
            };
        }
        return {
            cancellable_method: cancellable_method
        };
    }).factory("Packages", function ($resource, $q) {
        return $resource("/rest/packages/?", {}, {
            save: {
                async: false,
                method: 'POST',
                url: "/rest/packages/?",
                transformRequest: function (form, headersGetter) {
                    var headers = headersGetter();
                    headers['X-Progress-ID'] = form.x_progress_id;
                    var formData = new FormData();
                    formData.append("content_file", form.file);
                    formData.append("overwrite", true);
                    return formData;
                },
                headers: { 'Content-Type': undefined, "X-Progress-ID": '' }
            },
            bulkdelete: { method: 'POST', url: '/rest/bulkdeletepackage/?' } //data format = {“ids”: [1, 2, 3, 4 … n-1, n]}
        });
    }).factory("ContentManagement", function ($resource) {
        return $resource("/rest/contentmanagement/?", {}, {
            checkteachercontent: { method: 'POST', url: '/rest/contentmanagement/checkteachercontent/?' },
            checkcategories: { method: 'POST', url: '/rest/contentmanagement/checkcategories/?' },
            deleteteachercontent: { method: 'DELETE', url: '/rest/contentmanagement/deleteteachercontent/?' },
            deletecategories: { method: 'DELETE', url: '/rest/contentmanagement/deleteunusedcategories/?' }
        });
    }).factory("Patches", function ($resource) {
        return $resource("/rest/patch/?", {}, {
            save: {
                method: 'POST',
                url: "/rest/patch/?",
                transformRequest: function (form, headersGetter) {
                    var headers = headersGetter();
                    var formData = new FormData();
                    formData.append("content_file", form.file);
                    return formData;
                }, headers: { 'Content-Type': undefined }
            }
        });
        //}).factory("Tiles", function ($resource) {
        //    return $resource("/angularviews/tiles.json", {});
    }).factory("Tiles", function ($resource, $q) {
        return $resource("/rest/tiles/:id/?", {}, {
            query: { method: 'GET', params: { page_size: '5000' }, isArray: false },
            save: {
                method: 'POST',
                url: "/rest/tiles/?",
                transformRequest: function (form) {
                    var formData = new FormData();
                    for (var field in form.tiledata) {
                        //removed transformation, no longer required
                        formData.append(field, form.tiledata[field]);
                    }
                    //add file
                    formData.append("icon", form.file);
                    return formData;
                }, headers: { 'Content-Type': undefined }
            },
            update: {
                method: 'POST', url: "/rest/updatetile/:id/?", params: { id: '@id' }, transformRequest: function (form) {

                    //var data = angular.copy(origData);
                    //data.members = objToIdArray(data.members);
                    var formData = new FormData();
                    for (var field in form.tiledata) {
                        //removed transformation, no longer required
                        if (field === "icon") {
                            if (form.file) {
                                continue;
                            }
                        }
                        formData.append(field, form.tiledata[field]);
                    }
                    if (form.file) {
                        formData.append("icon", form.file);
                    }
                    return formData;

                }, headers: { 'Content-Type': undefined }
            },
            toggle: {
                method: 'PUT', params: { id: '@id' }, transformRequest: function (origData) {

                    var data = angular.copy(origData);
                    data.members = objToIdArray(data.members);
                    return angular.toJson(data);
                }
            },
            reorder: { method: 'POST', url: "/rest/reordertiles/?" },
            cancel: { method: 'POST', url: "/rest/cleanuptiles/?" }
        });
    }).factory("Database", function ($http) {
        return {
            getLatest: function () {
                return $http.get("/rest/database/latest").then(function (resp) {
                    return resp.data ? resp.data.date : '';
                });
            },
            restore: function () {
                return $http.get("/rest/database/restore");
            }
        };
    });

}());