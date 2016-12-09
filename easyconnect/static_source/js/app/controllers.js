/// <reference path="../../angularjs/angular.js" />
(function () {
    ////////////////////////////////////////
    //* Main wrapper controller to wrap common functionality
    ////////////////////////////////////////
    angular.module('ecControllers', []).controller("MainCtrl", ['$scope', 'userService', '$location', '$window', '$http', 'localStorageService', 'Settings',
        function ($scope, userService, $location, $window, $http, localStorageService, Settings) {
                        
            var auth_data = localStorageService.get('authorizationData')
            if (null != auth_data) {
                $http.defaults.headers.common['Authorization'] = 'Token ' + localStorageService.get('authorizationData')['token'];
                userService.authFromToken();
            }

            $scope.$location = $location;
            $scope.user = null;
            $scope.isTeacher = function () { return $scope.user.type === "teacher"; };
            $scope.working = false;

            var getCurrentSettings = function () {

                $scope.user = userService.get();

                Settings.checkLibrary(function (response) {
                    $scope.libhidden = response.library_hidden == 'True';
                });

                Settings.checkInternet(function (response) {
                    $scope.internet = response.internet > 0;
                });
            }

            getCurrentSettings();

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
                    $location.search({});
                    form.term.$setPristine();
                    if ($location.path().indexOf('lessons') > -1) {
                        $location.path("lessons").search('term', keywords);
                    } else {
                        $location.path("library/search").search('term', keywords);
                    }
                }
            };

            $scope.switchUserView = function (view) {
                $scope.user.type = view;
            };
            
            $scope.$on('user-authentication-changed', function () {
                getCurrentSettings();
            });

        }]).controller("SettingCtrl", ["$scope", 'Settings', 'toaster', function ($scope, Settings, toaster) {

            Settings.checkLibrary(function (response) {
                $scope.libhidden = response.library_hidden == 'True';
            });

            Settings.checkInternet(function (response) {
                $scope.internet = response.internet > 0;
            });

            $scope.toggleInternet = function () {
                Settings.toggleInternet(function (response) {
                    $scope.internet = response.internet > 0;
                    var msg = 'Internet ' + $scope.internet ? 'Enabled' : 'Disabled';
                    toaster.pop('success', msg);
                });
            };

            $scope.toggleLibrary = function () {
                Settings.toggleLibrary(function (response) {
                    $scope.libhidden = response.library_hidden == 'True';
                    var msg = 'Library ' + ($scope.libhidden? 'Hidden' : 'Shown');
                    toaster.pop('success', msg);
                });
            };

        }]).controller("SearchCtrl", ["$scope", "Search", '$routeParams', function ($scope, Search, $routeParams) {
            if ($routeParams.term) {
                $scope.searchPromise = Search.search({ 'data': $routeParams.term }, function (response) {
                    $scope.items = response.items;
                    $scope.lessons = respons.lessons;
                });
            }
        }]).controller("LoginCtrl", ["$scope", 'userService', '$routeParams', '$rootScope', 'localStorageService', function ($scope, userService, $routeParams, $rootScope, localStorageService) {
            $scope.login = function (username, password, form) {
                if (form.$valid) {
                    console.log(username);
                    userService.login(username, password).$promise.then(function (response) {
                        $rootScope.$broadcast('user-authentication-changed');
                        $scope.$location.path($routeParams.next);
                    });
                }
            };

        }]).controller("LogoutCtrl", ["$scope", 'userService', '$routeParams', 'localStorageService', '$rootScope', function ($scope, userService, $routeParams, localStorageService, $rootScope) {
            userService.logout(function (response) { $scope.user = { type: 'student', is_authenticated: false }; });
            $rootScope.$broadcast('user-authentication-changed');
            $scope.$location.path($routeParams.next);

        }]).controller("LessonCtrl", ['$scope', 'Lessons', '$routeParams', 'toaster', "Search", '$location', '_', 'SharedData', '$window', '$q',
    function ($scope, Lessons, $routeParams, toaster, Search, $location, _, SharedData, $window, $q) {
        var query = {};
            $scope.checkedLessons = [];
            $scope.checkedItems = [];
            $scope.breadcrumbs = {};

            $scope.init = function (param) {
                query = param;
                if (!$routeParams.page && !$routeParams.term)
                    refreshlist();
            };

            if ($routeParams.Id) {
                Lessons.get({ id: $routeParams.Id }, function (response) {
                    $scope.lesson = response;
                });
            }
           
            if ($routeParams.page) {
                query = query || {};
                query.page = $routeParams.page;
            }

            var refreshlist = function () {
                $scope.lessonsPromise = Lessons.get(query, function (data) {
                    $scope.lessons = data;
                }).$promise;
            };

            if ($routeParams.term) {
                query.search = $scope.breadcrumbs.search = $routeParams.term;
                refreshlist();

            } else {
                $scope.breadcrumbs.search = null;
                query.search = null;
            }

            $scope.page = function (pageNum) {
                query = query || {};
                query.page = pageNum
                refreshlist();
            }

            $scope.featuretoggle = function (lesson) {
                $scope.working = true;
                lesson.featured = !lesson.featured;
                $scope.lessonsPromise = Lessons.update(lesson, function () {
                    if (query) refreshlist();
                    $scope.working = false;
                    toaster.pop('success', lesson.featured ? 'Featured' : 'Unfeatured');
                }).$promise;

            };

            $scope.checkedtoggle = function (lesson) {
                var found = false;
                for (var i = 0, len = $scope.checkedLessons.length; i < len; i++) {
                    if (lesson.id === $scope.checkedLessons[i].id) {
                        $scope.checkedLessons.splice(i, 1);
                        found = true;
                        break;
                    }
                }
                if (!found) $scope.checkedLessons.push(lesson);

                //SharedData.checkedContentItems = $scope.checkedItems;
                //$rootScope.$broadcast('checked-items-changed');
            };

            $scope.toggleForm = function (show) {
                $scope.showForm = show;
                $scope.newLesson = '';
            };

            $scope.addLesson = function (title) {

                if (title) {
                    var newLesson = new Lessons({ 'title': title });
                    newLesson.$save(function (success) {
                        toaster.pop('success', 'Lesson added');
                        refreshlist();
                        $scope.toggleForm(false);
                    });
                }
            };

            $scope.update = function (lesson, form) {
                if (lesson.title) {
                    $scope.lessonsPromise = Lessons.update(lesson, function () {
                        toaster.pop('success', 'Title Updated');
                    }).$promise;
                }
            };

            $scope.remove = function (lesson) {
                var del = $window.confirm('Are you sure you want to delete?');
                if (del) {
                    $scope.lessonsPromise = Lessons.remove({ id: lesson.id }, function (response) {
                        toaster.pop('success', 'Lesson Deleted');
                        refreshlist();
                    }).$promise;
                }
            };

            $scope.removeItems = function () {
                if ($scope.checkedItems && $scope.checkedItems.length) {
                    var del = $window.confirm('Are you sure you want to remove these items?');
                    if (del) {
                        $scope.lesson.members = _.reject($scope.lesson.members, function (item) { return _.find($scope.checkedItems, function (checked) { return item.id === checked.id; }) != null });
                        $scope.checkedItems = [];
                        $scope.lessonsPromise = Lessons.update($scope.lesson, function (response) {
                            toaster.pop('success', 'Items Removed');
                        }).$promise;
                    }
                }
            };
            
            $scope.batchDelete = function () {

                if ($scope.checkedLessons.length) {
                    var del = $window.confirm('Are you sure you want to delete these lessons?');
                    if (del) {
                        var promises = [];
                        for (var i = 0, len = $scope.checkedLessons.length; i < len; i++) {
                            promises.push(Lessons.remove({ id: $scope.checkedLessons[i].id }).$promise);
                        }
                        $q.all(promises).then(function () {
                            toaster.pop('success', 'Lessons Deleted');
                            refreshlist();
                        });
                    }
                }
            };

            $scope.$on('checked-items-changed', function () {
                $scope.checkedItems = SharedData.checkedContentItems;
            });

    }]).controller("ContentItemCtrl", ["$scope", "ContentItems", '$routeParams', '$location', 'Lessons', 'toaster', '_', 'SharedData', 'Categories', '$rootScope', '$window',
            function ($scope, ContentItems, $routeParams, $location, Lessons, toaster, _, SharedData, Categories, $rootScope, $window) {
            var query = {};
            $scope.checkedItems = [];
            $scope.editing = false;
            $scope.embedded = true;
            $scope.inLessons = $location.path().indexOf("lessons") > -1;
            $scope.content = {};
            $scope.expanded = [];

            if ($routeParams.id && !$scope.inLessons) {
                $scope.editing = true;
                ContentItems.get({ id: $routeParams.id }, function (response) {
                    $scope.content = response;
                    if (response.categories && response.categories.length) {
                        var category = response.categories[0];
                        if (category.parent === null)
                            $scope.content.category1 = category;
                        else {
                            Categories.get({ id: category.parent }, function (response) {
                                if (response.parent === null) {
                                    $scope.content.category2 = category;
                                    $scope.content.category1 = response;
                                } else {
                                    Categories.get({ id: response.parent }, function (inner_response) {
                                        $scope.content.category3 = category;
                                        $scope.content.category2 = response;
                                        $scope.content.category1 = inner_response;
                                    });
                                }
                            });
                        }
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

            $scope.expandtoggle = function (item) {
                var pos = $scope.expanded.indexOf(item.id);
                if (pos > -1) {
                    $scope.expanded.splice(pos, 1);
                } else {
                    $scope.expanded.push(item.id);
                }
            };

            $scope.featuretoggle = function (item) {
                $scope.working = true;
                item.featured = !item.featured;
                $scope.contentItemsPromise = ContentItems.update(item, function () {
                    refreshlist();
                    $scope.working = false;
                    toaster.pop('success', item.featured ? 'Featured' : 'Unfeatured');
                }).$promise;
            };

            $scope.hidetoggle = function (item) {
                $scope.working = true;
                item.hidden = !item.hidden;
                $scope.contentItemsPromise = ContentItems.update(item, function () {
                    refreshlist();
                    $scope.working = false;
                    toaster.pop('success', item.hidden ? 'Hidden' : 'Visible');
                }).$promise;
            };

            $scope.remove = function (item) {
                var del = $window.confirm('Are you sure you want to delete?');
                if (del) {
                    $scope.contentItemsPromise = ContentItems.remove({ id: item.id }, function (response) {
                        toaster.pop('success', 'Item Deleted');
                        refreshlist();
                    }).$promise;
                }
            };

            $scope.save = function (contentItem, form) {
                if (form.$valid) {
                    ContentItems.update(contentItem, function (success) {
                        toaster.pop('success', 'Item successfully updated');
                        $scope.$location.path("library").search("uploaded", true);
                    });
                }
            };

            $scope.addToLesson = function (item) {
                var existing = _.find($scope.lesson.members, function (lessonitem) { return lessonitem.id == item.id });
                if (!existing) {
                    $scope.lesson.members.push(item);
                    Lessons.update($scope.lesson, function (response) {
                        toaster.pop('success', 'Item added to ' + $scope.lesson.title);
                    });
                } else {
                    toaster.pop('warning', 'Item already in list');
                }
            };

            $scope.checkedtoggle = function (item) {
                var found = false;
                for (var i = 0, len = $scope.checkedItems.length; i < len; i++) {
                    if (item.id === $scope.checkedItems[i].id) {
                        $scope.checkedItems.splice(i, 1);
                        found = true;
                        break;
                    }
                }
                if (!found) $scope.checkedItems.push(item);

                SharedData.checkedContentItems = $scope.checkedItems;
                $rootScope.$broadcast('checked-items-changed');
            };

            }
    ]).controller("LibraryCtrl", ['$scope', 'ContentItems', '$routeParams', 'Lessons', 'toaster', '_', 'SharedData', "Search", '$window', '$q',
        function ($scope, ContentItems, $routeParams, Lessons, toaster, _, SharedData, Search, $window, $q) {
            var query = {};
            $scope.lesson = null;
            $scope.lessons = null;
            $scope.lesson_contents = [];
            $scope.isUploaded = $routeParams.uploaded || false;
            $scope.isPreloaded = $routeParams.preloaded || false;
            $scope.breadcrumbs = {};

            $scope.hideMe = function () {
                $scope.lesson_contents.length > 0;
            };

            $scope.init = function () {
                if ($scope.isPreloaded === false && $scope.isUploaded === false) $scope.isPreloaded = true; //Preloaded is the default
                if (!$routeParams.term) {
                    getUploaded();
                    getPreloaded();
                }
                Lessons.get({'page_size' : 1000}, function (response) {
                    $scope.lessons = response.results;
                });
            };

            if ($routeParams.lesson) {
                Lessons.get({ id: $routeParams.lesson }, function (response) {
                    $scope.lesson = response;
                    $scope.lesson_contents = response.members;
                });
            }



            if ($routeParams.t) {
                query.t = $routeParams.t;
            } else {
                $scope.breadcrumbs.tag = null;
            }
            
            if ($routeParams.c) {
                query.c = $routeParams.c;
            } else {
                for (var i = 3; i > 0; i--) {
                    $scope.breadcrumbs['category' + i] = null;
                }
            }

            var getUploaded = function (q) {
                if ($scope.isTeacher()) {
                    q = q || angular.copy(query || {});
                    q.uploaded = "True";

                    $scope.uploadedPromise = ContentItems.get(q, function (data) {
                        $scope.uploaded_items = data;
                    }).$promise;
                }
            };

            var getPreloaded = function (q) {
                q = q || angular.copy(query || {});
                if ($scope.isTeacher())
                    q.uploaded = "False";
                else {
                    $scope.isPreloaded = true;
                    q.uploaded = null;
                }

                $scope.preloadedPromise = ContentItems.get(q, function (data) {
                    $scope.preloaded_items = data;
                }).$promise;
            };

            if ($routeParams.term) {
                $scope.breadcrumbs.search = $routeParams.term;
                query.search = $routeParams.term
                getPreloaded();
                getUploaded();
                //$scope.uploadedPromise = Search.contentItems({ 'data': $routeParams.term, 'uploaded': 'True' }, function (response) {
                //    $scope.uploaded_items = { current_page: 1, next: null, page_total: 1, range_end: response.length, range_start: 1 };
                //    $scope.uploaded_items.count = response.length;
                //    $scope.uploaded_items.results = response;
                //}).$promise;

                //$scope.preloadedPromise = Search.contentItems({ 'data': $routeParams.term, 'uploaded': 'False' }, function (response) {
                //    $scope.preloaded_items = { current_page: 1, next: null, page_total: 1, range_end: response.length, range_start: 1 };
                //    $scope.preloaded_items.count = response.length;
                //    $scope.preloaded_items.results = response;
                //}).$promise;
            } else {
                $scope.breadcrumbs.search = null;
            }

            $scope.page = function (pageNum) {
                var q = angular.copy(query || {});
                q.page = pageNum
                if ($scope.isUploaded)
                    getUploaded(q);
                else
                    getPreloaded(q);
            }

            $scope.$on('checked-items-changed', function () {
                $scope.checkedItems = SharedData.checkedContentItems;
            });

            $scope.batchAdd = function (selectedLesson) {
                var checkedItems = SharedData.checkedContentItems;

                if (checkedItems.length) {
                    if (!$scope.lesson && !selectedLesson) {
                        toaster.pop('warning', "No Lesson selected");
                        return;
                    }

                    $scope.lesson = selectedLesson || $scope.lesson;

                    angular.forEach(checkedItems, function (item) {
                        var existing = _.find($scope.lesson.members, function (member) { return typeof member === 'object' ? member.id === item.id : member === item.id; });
                        if (!existing)
                            this.push(item);
                    }, $scope.lesson.members);

                    Lessons.update($scope.lesson, function (update_response) {
                        Lessons.get({ id: update_response.id }, function (response) {
                            toaster.pop('success', 'Items added to ' + $scope.lesson.title);
                            $scope.lesson = response;

                            $scope.lesson_contents = response.members;
                            SharedData.checkedContentItems = [];
                        });
                    });
                }
            };

            $scope.batchDelete = function () {

                if ($scope.checkedItems.length) {
                    var del = $window.confirm('Are you sure you want to delete these Items?');
                    if (del) {
                        var promises = [];
                        for (var i = 0, len = $scope.checkedItems.length; i < len; i++) {
                            promises.push(ContentItems.remove({ id: $scope.checkedItems[i].id }).$promise);
                        }
                        $q.all(promises).then(function () {
                            toaster.pop('success', 'Items Deleted');
                            getUploaded();
                        });
                    }
                }
            };

            $scope.addToLesson = function (item) {

                if (!$scope.lesson) {
                    toaster.pop('warning', 'No Lesson selected');
                    return;
                }

                var existing = _.find($scope.lesson.members, function (lessonitem) { return lessonitem.id == item.id });
                if (!existing) {
                    $scope.lesson.members.push(item);
                    Lessons.update($scope.lesson, function (response) {
                        toaster.pop('success', 'Item added to ' + $scope.lesson.title);
                    });
                } else {
                    toaster.pop('warning', 'Item already in list');
                }
            };

            $scope.switchview = function (view) {
                if ((view === 'uploaded' && $scope.isPreloaded) || (view === 'preloaded' && $scope.isUploaded)) {
                    $scope.isPreloaded = !$scope.isPreloaded;
                    $scope.isUploaded = !$scope.isUploaded;
                }
                //$scope.$location.search(view);
            };

            $scope.tagFilter = function (tag) {
                query.t = tag.id;
                getUploaded();
                getPreloaded();
                var params = $scope.$location.search();
                params.term = null;
                params.t = tag.id
                $scope.breadcrumbs.search = null;
                $scope.breadcrumbs.tag = tag;
                $scope.$location.path('library').search(params);                
            };

            $scope.categoryFilter = function (selectedCategory) {
                if (selectedCategory.category3)
                    query.c = selectedCategory.category3.id;
                else if (selectedCategory.category2)
                    query.c = selectedCategory.category2.id;
                else if (selectedCategory.category1)
                    query.c = selectedCategory.category1.id;
                else {
                    toaster.pop('warning', 'No category selected');
                    return;
                }
                $scope.breadcrumbs.search = null;

                getUploaded();
                getPreloaded();
                var params = $scope.$location.search();
                params.c = query.c;
                params.term = null;
                for (var i = 1; i < 4; i++) {
                    $scope.breadcrumbs['category' + i] = selectedCategory['category' + i];
                }
                $scope.$location.path('library').search(params);
            };

            $scope.replaceFilter = function (param, value) {
                if (param) {
                    if (isNaN(param))
                        $scope.breadcrumbs.search = null;
                    else {
                        $scope.breadcrumbs.tag = null;
                        $scope.breadcrumbs.search = null;

                        for (var i = 3; i > +param; i--) {
                            $scope.breadcrumbs['category' + i] = null;
                        }
                        query.c = value;
                    }
                } else {
                    $scope.breadcrumbs = {};
                    query.c = null;
                }

                if (isNaN(param))
                    query.search = null;
                else {
                    query.t = null;
                    query.search = null;

                }
                getUploaded();
                getPreloaded();
                $scope.$location('library').search(query);
            }

        }]).controller("TagCtrl", ['$scope', 'Tags', '$q', '$filter',
    function ($scope, Tags, $q, $filter) {

        var refreshlist = function () {
            $scope.tagsPromise = Tags.query(function (data) {
                $scope.tags = data;
            }).$promise;

        };

        refreshlist();

        $scope.addTag = function (tag) {
            if (tag && !tag.id) {
                var newTag = new Tags({ id: 0, text: tag.text });
                newTag.$save(function (response) {
                    $scope.tags.push(response);
                    for (var i = 0, len = $scope.content.tags.length; i < len; i++) {
                        if ($scope.content.tags[i].text === response.text) {
                            $scope.content.tags[i] = response;
                            break;
                        }
                    }
                });
            }
        };

        $scope.lookupTag = function (q) {
            return $q.when($filter('filter')($scope.tags, { text: q }));
        };

        $scope.update = function (tag, form) {
            if (tag.text) {
                $scope.tagsPromise = Tags.update(tag).$promise;
            }
        };

        $scope.remove = function (tagId) {
            var del = $scope.$window.confirm('Are you sure you want to delete?');
            if (del) {
                $scope.tagsPromise = Tags.remove({ id: tagId }, function (response) {
                    refreshlist();
                }).$promise;
            }
        };

    }]).controller("CategoryCtrl", ['$scope', 'Categories', 'Categorytree',
    function ($scope, Categories, Categorytree) {
        $scope.init = function (type) {
            refreshlist(type);
        };

        var refreshlist = function (type) {
            if (type == 'tree')
                $scope.categoriesPromise = Categorytree.get(function (data) {
                    $scope.categories = data;
                }).$promise;
            else
                $scope.categoriesPromise = Categories.query(function (data) {
                    $scope.categories = data;
                }).$promise;
        };


        $scope.addCategory = function (parent, form) {

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
            if (name) {
                category.name = name;
                if (category.id)
                    $scope.categoriesPromise = Categories.update(category).$promise;
                else
                    $scope.categoriesPromise = Categories.save(category, function (response) {
                        refreshlist('tree');
                    }).$promise;

            } else {
                return "name required";
            }
        };

        $scope.remove = function (category) {
            if (category) {
                if (category.id) {
                    var del = $scope.$window.confirm('Are you sure you want to delete?');
                    if (del) {
                        $scope.categoriesPromise = Categories.remove({ id: category.id }, function (response) {
                            refreshlist('tree');
                        }).$promise;
                    }
                } else {
                    refreshlist('tree');
                }
            } else {
                return "nothing to remove";
            }
        }
    }]).controller("UploadCtrl", ["$scope", 'ContentItems', 'toaster',
        function ($scope, ContentItems, toaster) {
        $scope.content = {};

        $scope.$on("fileSelected", function (event, args) {
            $scope.$apply(function () {
                //add the file object to the scope's files collection
                $scope.content_file = args.file;
                $scope.filename = args.file.name
                $scope.content.title = $scope.filename.substr(0, $scope.filename.lastIndexOf("."));
            });
        });

        $scope.save = function (metadata, form, file) {
            formobj = {};
            formobj.metadata = angular.copy(metadata);
            formobj.file = file;
            if (form.$valid) {
                ContentItems.save(formobj, function (success) {
                    toaster.pop('success', 'Item successfully uploaded');
                    $scope.$location.path("library").search("uploaded", true);
                });
            }
        };
    }]);
}());