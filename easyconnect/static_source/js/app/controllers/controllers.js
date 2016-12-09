/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //* Header controller to wrap common functionality
    ////////////////////////////////////////
    angular.module('ecControllers', []).controller("HeaderCtrl", ['$scope', '$window', '$location', 'Settings', 'toaster', 'AUTH_EVENTS', 'APP_EVENTS', '$rootScope',
        function ($scope, $window, $location, Settings, toaster, AUTH_EVENTS, APP_EVENTS, $rootScope) {

            $scope.showNavContainer = false;
            $scope.showSubManageMenu = false;

            $scope.tabActive = function (route) {
                if (route.length > 2) {
                    return $location.path().indexOf(route) > -1;
                }
                return $location.path() == route;
            };

            $scope.keywords = {};
            $scope.search = function (keywords, form) {
                if (keywords) {
                    $scope.keywords = {};
                    form.term.$setPristine();

                    if ($location.path().indexOf('lessons') > -1) {
                        $location.path("/lessons").search('search', keywords);
                    } else if ($location.path().indexOf('/library') > -1) {
                        var params = $location.search();
                        params.search = keywords;
                        $location.path("/library").search(params);
                    } else {
                        $location.path("/library").search('search', keywords);
                    }
                }
            };

            $scope.toggleLibrary = function () {
                Settings.toggleLibrary(function (response) {
                    $scope.libhidden = response.library_hidden;
                    var msg;
                    if ($scope.libhidden) {
                        msg = gettext("Library Hidden From Students");
                    }
                    else {
                        msg = gettext("Library Visible To Students");
                    }
                    toaster.pop('success', msg);
                    $rootScope.$broadcast(APP_EVENTS.settingsChanged);
                });
            };

            var checkLibraryAccess = function () {
                Settings.checkLibrary(function (response) {
                    $scope.libhidden = response.library_hidden;
                });
            };

            checkLibraryAccess();

            $scope.$on(APP_EVENTS.settingsChanged, function () {
                checkLibraryAccess();
            });

            $scope.$on(AUTH_EVENTS.authenticationChanged, function () {
                checkLibraryAccess();
            });

            $scope.switchUserView = function (view) {
                Settings.toggleViewType({ 'type': view }, function (response) {
                    $scope.user.type = view;
                    $location.path('/');
                });
            };

            $scope.showManageMenu = function (event) {
                $scope.showSubManageMenu = true;
            };

            $scope.hideManageMenu = function (event) {
                $scope.showSubManageMenu = false;
                $scope.showNavContainer = false;
            };

            $scope.toggleNavContainer = function () {
                $scope.showNavContainer = !$scope.showNavContainer;
            };
        }
    ]).controller("AdminCtrl", ['$scope', 'Settings', 'toaster', 'APP_EVENTS', '$rootScope', 'FIELD_VAL', 'userService', '$window',
        function ($scope, Settings, toaster, APP_EVENTS, $rootScope, FIELD_VAL, userService, $window) {
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.SSID = '';
            $scope.resettingAccount = false;

            $scope.resetTeacherAccount = function () {
                var del = $window.confirm(gettext("Are you sure you want to reset the Teacher account?"));
                if (del) {
                    $scope.resettingAccount = true;
                    Settings.resetTeacherAccount({}, function (response) {
                        $scope.$apply(function () {
                            $scope.resettingAccount = false;
                        });
                        if (response.success !== 'True') {
                            toaster.pop('error', gettext("The teacher account was not reset."));
                        }
                        else {
                            toaster.pop('success', gettext("Teacher account reset."));
                        }
                    });
                }
            }
        }
    ]).controller("TagCtrl", ['$scope', 'Tags', '$q', '$filter', '$window', '$location',
    function ($scope, Tags, $q, $filter, $window, $location) {
        $scope.$location = $location;
        $scope.tags = [];
        $scope.preloadedTags = [];
        $scope.uploadedTags = [];
        var UseTwoLists = false;
        var validationTags = [];

        var maxUses = Number.NEGATIVE_INFINITY, minUses = Number.POSITIVE_INFINITY, max_minus_min;
        $scope.init = function (param, twoLists) {
            UseTwoLists = twoLists;
            refreshlist(param);
        }

        var refreshlist = function (param) {
            if (UseTwoLists) {
                param.locked = 'true';
                Tags.query(param, function (data) {
                    $scope.preloadedTags = data.results;
                    validationTags = validationTags.concat($scope.preloadedTags);
                });
                param.locked = 'false';
                Tags.query(param, function (data) {
                    $scope.uploadedTags = data.results;
                    validationTags = validationTags.concat($scope.uploadedTags);
                });

            }
            else {
                Tags.query(param, function (data) {
                    $scope.tags = data.results;
                    validationTags = $scope.tags;
                });
            }
        };

        //Calculate min and max when tags changes
        $scope.$watch('tags', function () {
            var tmp;
            for (var i = 0, len = $scope.tags.length; i < len; i++) {
                tmp = $scope.tags[i].uses;
                if (tmp < minUses) minUses = tmp;
                if (tmp > maxUses) maxUses = tmp;
            }

            if (minUses > maxUses)
                minUses = maxUses = 0;

            max_minus_min = maxUses - minUses;
            max_minus_min = max_minus_min > 0 ? max_minus_min : 1;
        });

        $scope.addTag = function (tag) {
            if (tag && !tag.id) {
                //don't need to sanitize tag on add as this is performed in the tag plugin
                var newTag = new Tags({ id: 0, text: tag.text });
                $scope.working = true;
                newTag.$save(function (response) {
                    $scope.tags.push(response);
                    for (var i = 0, len = $scope.content.tags.length; i < len; i++) {
                        if ($scope.content.tags[i].text === response.text) {
                            $scope.content.tags[i] = response;
                            break;
                        }
                    }
                }).then(function () { $scope.working = false; });
            }
        };

        $scope.lookupTag = function (q) {
            return $q.when($filter('filter')($scope.tags, { text: q }));
        };

        $scope.validate = function (tag, text, form) {
            if (text) {
                text = sanitize(text).toUpperCase();
                var existing = _.find(validationTags, function (t) { return t.text.toUpperCase() === text && tag.id != t.id });
                if (existing) {
                    return gettext("Duplicate");
                }
                tag.text = text;
            } else {
                return gettext("This is a required field");
            }
        }

        $scope.update = function (tag, form) {
            if (tag.text) {
                tag.text = sanitize(tag.text);
                $scope.tagsPromise = Tags.update(tag).$promise;
            }
        };

        $scope.remove = function (tagId) {
            var del = $window.confirm(gettext("Are you sure you want to delete?"));
            if (del) {
                $scope.tagsPromise = Tags.remove({ id: tagId }, function (response) {
                    refreshlist({ page_size: 5000 });
                }).$promise;
            }
        };

        $scope.calculateScore = function (tag) {
            if (tag.uses > 0){
                var score = Math.round(((tag.uses - minUses) / max_minus_min) * 7);
                return score > 0 ? score : 1;
            }
            return 0;
        };

        var sanitize = function (text) {
            if (!text)
                return '';

            return text.replace(/^\s+|\s+$/gm, '').replace(/\s/g, '-');
        };


    }]).controller("CategoryCtrl", ['$scope', 'Categories', 'Categorytree', '$window', '$q', '_', 'FIELD_VAL',
    function ($scope, Categories, Categorytree, $window, $q, _, FIELD_VAL) {

        $scope.inserted = null;

        $scope.init = function (type) {
            refreshlist(type);
        };

        var refreshlist = function (type) {
            if (type == 'tree') {
                $scope.inserted = null;
                $scope.categoriesPromise = Categorytree.get(function (data) {
                    $scope.categories = data;
                }).$promise;
            } else {
                $scope.categoriesPromise = Categories.query(function (data) {
                    $scope.categories = data;
                }).$promise;
            }
        };

        $scope.addCategory = function (parent, form) {
            //only show one insert form at a time
            if ($scope.inserted)
                return;
            var parentId = parent ? parent.id : null;

            $scope.inserted = {
                id: 0,
                name: '',
                parent: parentId,
                uses: 0,
                children: []
            };
            if (parent) {
                parent.children.push($scope.inserted);
            } else {
                $scope.categories.results.push($scope.inserted);
            }
        };

        $scope.save = function (category, name, form) {
            if (name.text) {
                category.name = sanitize(name.text);
                if (category.id)
                    $scope.categoriesPromise = Categories.update(category).$promise;
                else
                    $scope.categoriesPromise = Categories.save(category, function (response) { refreshlist('tree'); }).$promise;

                $scope.inserted = null;

                return $scope.categoriesPromise;

            } else {
                return $q.when(gettext("name required"));
            }
        };

        $scope.validate = function (data, current, parent) {
            if (!data) {
                return gettext("name required");
            }

            data = sanitize(data).toUpperCase();

            if (data.length > FIELD_VAL.categoryMax) {
                return interpolate(gettext("only %(max)s characters allowed"), { max: FIELD_VAL.categoryMax }, true);
            }

            var list = parent ? parent.children : $scope.categories.results;
            var existing = _.find(list, function (cat) {
                return cat.name.toUpperCase() === data && current.id != cat.id
            });
            if (existing)
                return gettext("Duplicate");
        };

        $scope.cancel = function (data) {
            if (data) {
                if (data.id === 0 && $scope.inserted != null) {
                    refreshlist('tree');
                }
            }
        };

        $scope.remove = function (category) {
            if (category) {
                if (category.id) {
                    var del = $window.confirm(gettext("Are you sure you want to delete?"));
                    if (del) {
                        $scope.categoriesPromise = Categories.remove({ id: category.id }, function (response) {
                            refreshlist('tree');
                        }).$promise;
                        return $scope.categoriesPromise;
                    }
                } else {
                    refreshlist('tree');
                }

            } else {
                return $q.when(gettext("nothing to remove"));
            }
        }

        var sanitize = function (text) {
            if (!text)
                return '';

            return text.replace(/^\s+|\s+$/gm, '');
        }

    }]).controller("UsbCtrl", ["$scope", "$route", 'USB', 'toaster',
        function ($scope, $route, USB, toaster) {
            $scope.content = {};
            $scope.working = false;
            $scope.tree_ready = false;
            $scope.upload_error = false;
            $scope.error_message = '';
            $scope.category = 0;
            $scope.show_meta = true; //false; removed toggle temporarily
            $scope.meta_changed = false;
            $scope.actual_files = [];
            $scope.file_title_mapping = [];
            $scope.tree_dirty = false;

            $scope.reload_disabled = true;

            $scope.reload_page = function () {
                $('#usb_browser').remove();
                $route.reload();
            }

            $scope.$on('$destroy', function () {
                $(window).off('beforeunload');
            });
            $(window).on('beforeunload', function (e) {
                if ($scope.tree_dirty) {
                    var message = gettext('If you leave this page all unsaved changes will be lost, are you sure?');
                    e.returnValue = message;
                    return message;
                }
            });
            $scope.$on('$locationChangeStart', function (event) {
                if (!$scope.tree_dirty) return;
                var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                if (!answer) {
                    event.preventDefault();
                }
            });

            $scope.selectCategory = function (selectedCategory) {
                $scope.category = selectedCategory.id
            };

            $scope.clearCategory = function () {
                $scope.category = 0;
            };

            $scope.toggleMetadata = function () {
                //$scope.show_meta = !$scope.show_meta;
            };

            $scope.onFileSelect = function () {
                $scope.tree_dirty = true;
                $scope.file_title_mapping = [];
                $scope.fileErrors = [];
                $scope.actual_files = [];

                var selected_id_list = $.jstree.reference('#usb_browser').get_selected();
                $scope.tree_ready = (selected_id_list.length > 0) ? true : false;

                var tmp = []
                //create a mapping for each file id to new title.
                for (var i = 0; i < selected_id_list.length; i++) {
                    var elm = $.jstree.reference('#usb_browser').get_json(selected_id_list[i]);
                    //only add if file
                    if (elm.icon == 'jstree-file') {
                        $scope.actual_files.push(selected_id_list[i]);
                        var title = elm.text.substr(0, elm.text.lastIndexOf("."));
                        tmp.push({ 'filename': elm.text, 'title': title, 'path': selected_id_list[i], 'uploaded': false, 'error': false });
                    }
                }
                $scope.file_title_mapping = tmp;
                $scope.$apply();
            };

            $scope.submitUSB = function () {
                $scope.working = true;
                $('.uploadcomplete-false').css('display', 'block');

                var total_count = $scope.actual_files.length;
                _.each($scope.actual_files, function (single_file, index) {
                    var formdata = {};
                    var title = _.find($scope.file_title_mapping, function (map) {
                        return single_file == map.path
                    }).title;

                    formdata.title = title; //add the updated title
                    formdata.selected = [$scope.actual_files[index]];
                    formdata.tags = $scope.content.tags;
                    formdata.description = $scope.content.description;
                    formdata.categories = [];
                    if ($scope.category && $scope.category != '-1') {
                        formdata.categories.push($scope.category);
                    }

                    $scope.usbUploadPromise = USB.uploadContent(formdata, function (response) {
                        if (response['result'] == 'success') {
                            _.find($scope.file_title_mapping, function (map) {
                                if (single_file == map.path) {
                                    map.uploaded = true;
                                }
                            });
                            toaster.pop('success', gettext("Item(s) successfully uploaded"));
                            total_count = total_count - 1;
                            if (total_count <= 0) {
                                $scope.working = false;
                                $scope.$destroy(); //call destroy to unbind the dirty bit
                                $scope.$location.path("library").search({ "uploaded": true, "ordering": "-date_added" });
                            }
                        }
                        else if (response["result"] === 'error' && response["type"] === "out_of_space") {
                            toaster.pop('error', gettext("There is not enough space on the internal drive.  Please connect external drive and retry."));
                        }
                        else
                        {
                            _.find($scope.file_title_mapping, function (map) {
                                if (single_file.name == map.filename) {
                                    map.error = true;
                                }
                            });
                            total_count = total_count - 1;
                            if (total_count <= 0) {
                                $scope.working = false;
                            }
                        }
                    }).$promise;
                });//endeach

            };

        }]).controller("CategoryHierarchyCtrl", ["$scope", 'Categorytree',
        function ($scope, Categorytree, toaster) {
            $scope.content = {};
            $scope.working = false;
            $scope.tree_ready = false;
            $scope.error_message = '';
            $scope.selected_id = '0';

            Categorytree.get(function (response) {
                $scope.tree = response;
            });

        }]);
}());