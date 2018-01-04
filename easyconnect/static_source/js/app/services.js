/// <reference path="../../angularjs/angular.js" />
(function () {
    angular.module("ecServices", ['ngResource'])
    .factory('Search', function ($resource) {
        return $resource("/rest/search/:type/?", {},
        {
            lessons: { method: 'POST', params: { type: 'lessons' }, isArray : true },
            contentItems: { method: 'POST', params: { type: 'contentitems' }, isArray: true }
        });
    }).factory('Lessons', function ($resource) {
        return $resource("/rest/lessons/:id/?", {}, {
            update: {
                method: 'PUT', params: { id: '@id' }, transformRequest: function (origData) {
                    var data = angular.copy(origData);
                    if (data.members && data.members.length > 0) {
                       
                            var tmp = [];
                            for (var i = 0, len = data.members.length; i < len; i++) {
                                tmp.push(typeof data.members[i] === 'object' ? data.members[i].id : data.members[i]);
                            }
                            data.members = tmp;
                        
                    }
                    return angular.toJson(data);
                }
            },
            query: { method: 'GET', isArray: false },
            save: { method: 'POST', url: "/rest/lessons/?" }

        });
    }).factory('ContentItems', function ($resource) {

        var contentTransform = function (origData, headersGetter, asObject) {
            var data = angular.copy(origData);
            asObject = asObject || false;
            if (data.tags && data.tags.length > 0) {
                var tmp = [];
                for (var i = 0, len = data.tags.length; i < len; i++) {
                    tmp.push(typeof data.tags[i] === 'object' ? data.tags[i].id : data.tags[i]);
                }
                data.tags = tmp;
            }

            if (data.categories && data.categories.length > 0) {
                var tmp = [];
                for (var i = 0, len = data.categories.length; i < len; i++) {
                    tmp.push(data.categories[i] === 'object' ? data.categories[i].id : data.categories[i]);
                }
                data.categories = tmp;
            }

            if (data.category3)
                data.categories = [data.category3.id];
            else if (data.category2)
                data.categories = [data.category2.id];
            else if (data.category1)
                data.categories = [data.category1.id];

            if (!asObject) {
                return angular.toJson(data);
            }
            else {
                return data;
            }
        };

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

                    if (form.metadata[category3Field])
                        form.metadata['categories'] = [form.metadata[category3Field].id];
                    else if (form.metadata[category2Field])
                        form.metadata['categories'] = [form.metadata[category2Field].id];
                    else if (form.metadata[category1Field])
                        form.metadata['categories'] = [form.metadata[category1Field].id];

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
                }, headers: { 'Content-Type': undefined }, url: "/rest/contentitems/?"

            },
            update: {
                method: 'PUT', params: { id: '@id' }, transformRequest: contentTransform
            },
            query: { method: 'GET', isArray: false, url: "/rest/contentitems/?" }

        });
    }).factory('Tags', function ($resource) {
        return $resource("/rest/tags/:id/?", {}, {
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
            toggleInternet: {
                method: 'POST', params: { 'setting': 'internet' }
            },
            toggleLibrary: {
                method: 'POST', params: { 'setting': 'library' }
            }

        });
    }).factory('_', function () {
        return window._; // assumes underscore has already been loaded on the page
    }).factory('SharedData', function () {
        var checkedContentItems = [];
        return {
            checkedContentItems: checkedContentItems
        };

    });;



    var userService = function ($http, $resource, localStorageService) {
        var auth_api_url = "/rest/auth\\/";
        var tokenauth_api_url = "/rest/tokenauth\\/";
        var user = {};
        user.username = '';
        user.is_authenticated = false;
        user.type = '';

        var auth = $resource(auth_api_url, {},
            {
                login: { method: 'POST' },
                logout: { method: 'DELETE' }
            });
        
        var token_auth = $resource(tokenauth_api_url, {},
            {
                login: { method: 'GET' }
            });

        return {
            login: function (username, password) {
                return auth.login({ 'username': username, 'password': password }, function (response) {

                    localStorageService.set('authorizationData', { token: response.token });
                    $http.defaults.headers.common['Authorization'] = 'Token ' + response.token;

                    user.is_authenticated = true;
                    user.type = "teacher";
                    //user.username = response.username;
                });
            },
            get: function () { return user; },
            logout: function () {
                return token_auth.login(function (response) {
                    console.log(response);
                    user.is_authenticated = false;
                    user.type = "student";
                    user.username = "";
                    localStorageService.set('authorizationData', null);
                });
            },
            authFromToken: function () {
                return token_auth.login(function (response) {
                    console.log(response);
                    user.is_authenticated = true;
                    user.type = "teacher";
                    user.username = response.username;
                });
            }
        };

    };

    var module = angular.module("ecApp");
    module.factory("userService", userService);

}());