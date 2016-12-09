/// <reference path="../../angularjs/angular.js" />
(function () {
    'use strict';
    ////////////////////////////////////////
    //*Tile controller
    ////////////////////////////////////////
    //angular.module('hubControllers', []).controller("TileCtrl", ['$scope', 'AUTH_EVENTS', 'APP_EVENTS', 'Tiles',
    //angular.module('ecControllers')
    angular.module('hubControllers', []).controller("TileCtrl", ["$scope", "$rootScope", 'toaster', "Tiles", '$window', 'APP_EVENTS', 'SharedData', '$route', '$routeParams', 'FIELD_VAL', '$location', 'Utils', 'USB', '$filter',
    function ($scope, $rootScope, toaster, Tiles, $window, APP_EVENTS, SharedData, $route, $routeParams, FIELD_VAL, $location, Utils, USB, $filter) {
        var leaveMessage = gettext('If you leave this page all unsaved changes will be lost and any content which has been imported will be removed from the device. Are you sure?');
        var query = {};
        $scope.working = false;
        $scope.tiles = [];

        $scope.editTile = {};
        $scope.showEdit = false;
        //$scope.showForm = false;
        $scope.visibleTileCount = 0;
        $scope.teacherTileCount = 0;
        $scope.$location = $location;
        $scope.FIELD_VAL = FIELD_VAL;

        $scope._form_url = false;
        $scope._form_usb = false;
        $scope._form_upload_complete = false;
        $scope.icon_file = [];
        $scope.formSubmitted = false;
        $scope.tmpImage = '';
        $scope.showUsb = true;

        var ieChecks = function () {
            //HACK for IE browsers that don't invoke the route change event for the add tile
            if (window.navigator.sayswho === 'IE 11') { 
                for (var i = 0, len = $scope.tiles.length; i < len; i++) {
                    if ($scope.tiles[i].url_target === '_self') $scope.tiles[i].formatted_url_string = $scope.tiles[i].url_string + "&rand=" + Math.floor((Math.random() * 1000000) + 1);
                }
            }
        };

        $scope.isDirty = function () {
            return $scope.addTileForm.$dirty || $scope.editTileForm.$dirty || $scope.icon_file.length;
        };

        $scope.makeClean = function () {
            $scope.addTileForm.$setPristine();
            $scope.editTileForm.$setPristine();
            $scope.iconMaxSizeError = undefined;
            $scope.iconTypeError = undefined;
            $scope.icon_file = [];
            $('form').find('input[type=file]').val('');
        };

        $scope.$on(APP_EVENTS.usbNotFound, function () {
            $scope.showUsb = false;
        });

        $scope.reload_page = function () {
            $('#tile_usb_browser').remove();
            $route.reload();
        }

        $scope.$on('$destroy', function () {
            $(window).off('beforeunload');
        });

        $(window).on('beforeunload', function (e) {
            if ($scope.isDirty()) {
                var message = leaveMessage;
                e.returnValue = message;
                return message;
            }
        });

        $scope.$on('$locationChangeStart', function (event) {
            if (!$scope.isDirty()) return;
            var answer = confirm(leaveMessage)
            if (!answer) {
                event.preventDefault();
            }
        });

        var refreshlist = function () {
            $scope.tiles = [];
            $scope.tileCount = 0;
            Tiles.query(function (response) {
                if (response.results) {
                    $scope.tiles = response.results;
                    $scope.visibleTileCount = _.where($scope.tiles, { teacher_tile: false, hidden: false }).length;
                    $scope.teacherTileCount = _.where($scope.tiles, { hidden: false }).length;
                }
                
                if ($scope.user.type == 'student'
                        && $scope.visibleTileCount <= $scope.FIELD_VAL.tileDefaultCount) {
                    //console.log('redirect---student');
                    //DAVEH - 15/09/2015 desicion made to NOT redirect from the landing page
                    //window.location = '/lessonplanner/#/';
                }
                else if ($scope.user.type == 'teacher'
                        && ($scope.visibleTileCount + $scope.teacherTileCount) <= $scope.FIELD_VAL.tileDefaultCountTeacher) {
                    //console.log('redirect---teacher');
                    //DAVEH - 15/09/2015 desicion made to NOT redirect from the landing page
                    //window.location = '/lessonplanner/#/';
                } else if ($scope.user.type == 'admin') {
                    $('#sortable').sortable({
                        placeholder: 'ui-state-highlight',
                        tolerance: 'pointer',
                        forceHelperSize: true,
                        forcePlaceholderSize: true,
                        helper: 'clone',
                        delay: 150,
                        containment: $('.sort_container'),
                        start: function (e, ui) {
                            ui.placeholder.height(ui.item.height() * 0.85);
                            ui.placeholder.width(ui.item.width() * 0.8);
                        },
                        //items: ".sortable_tile:not(.sort_disabled)", //only disables drag, can still sort other items between them
                        stop: function (event, ui) {
                            $scope.working = true;
                            var order = $(this).sortable('toArray');
                            Tiles.reorder({ ids: order }, function (response) {
                                $scope.working = false;
                            });

                        }
                    });
                }
                ieChecks();
                
            });
        };
        refreshlist();

        var resetQueryString = function () {
            var params = $location.search();
            if (params && params.createtile /*&& validationLessons.length === 0*/) {
                Utils.executeFn(function () {
                    params.createtile = null;
                    $location.search(params);
                });
                ieChecks();
            }
        }

        $scope.toggleForm = function (show, delete_content) {
            if (!show) {
                if ($scope.isDirty()) {
                    var answer = confirm(leaveMessage);
                    if (!answer) {
                        return false;
                    }
                    $scope.makeClean();
                }
                resetQueryString();
            }
            $scope.showForm = show;

            if (delete_content) {
                //cleanup
                Tiles.cancel({ 'storage_folder': $scope.newTile.storage_folder }, function (done) { });
            }

            $scope.newTile = {
                'teacher_tile': false,
                'hidden': false,
                'read_only': false
            };

            $scope._form_url = false;
            $scope._form_usb = false;

            $scope.formSubmitted = false;
            
        };

        $scope.toggle_tile_creation_method = function (usb, url) {
            $scope._form_usb = usb;
            $scope._form_url = url;
        }

        if ($routeParams.createtile) {
            $scope.toggleForm(true, false);
        }


        $scope.addTile = function (model, form) {

            if (form.$valid && $scope.icon_file.length && !$scope.isDuplicateTitle({id : 0}, model.title, form)) {

                if (model.storage_folder == '') {
                    console.log('storagenotset');
                    model.storage_folder = model.url_string; //if user has manually entered a url
                }

                var newTile = {
                    'title': model.title,
                    'url_string': model.url_string,
                    'teacher_tile': model.teacher_tile,
                    'hidden': model.hidden,
                    'read_only': false,
                    'storage_folder': model.storage_folder
                };

                var formObj = {};
                formObj.tiledata = newTile;
                formObj.file = $scope.icon_file[0];

                Tiles.save(formObj, function (success) {
                    toaster.pop('success', gettext("Tile added"));
                    $scope.makeClean();

                    $scope.toggleForm(false, false);
                    refreshlist();
                });

            } else {
                $scope.formSubmitted = true;
            }
        };

        $scope.updateTile = function (model, form) {
            if (form.$valid && !$scope.isDuplicateTitle(model, model.title, form) && $scope.iconMaxSizeError == null && $scope.iconTypeError == null) {

                    var tile = {
                        'id': model.id,
                        'title': model.title,
                        'url_string': model.url_string,
                        'icon': model.icon,
                        'teacher_tile': model.teacher_tile,
                        'hidden': model.hidden,
                        'read_only': model.read_only,
                        'display_order': model.display_order,
                        'storage_folder': model.storage_folder
                    };

                    var formObj = { id: model.id };
                    formObj.tiledata = tile;
                    if ($scope.icon_file[0]) {
                        formObj.file = $scope.icon_file[0];
                    }
                    Tiles.update(formObj, function (success) {
                        toaster.pop('success', gettext("Tile updated"));
                        $scope.makeClean();
                        $scope.toggleEdit({});
                        refreshlist();
                    });

            }
        };

        $scope.deleteTile = function (tile) {
            var del = $window.confirm(gettext("This tile and any associated imported content will be deleted from the device. Are you sure you want to delete?"));
            if (del) {
                $scope.tilePromise = Tiles.remove({ id: tile.id }, function (response) {
                    Tiles.cancel({ 'storage_folder': tile.storage_folder }, function (done) { });
                    toaster.pop('success', gettext("Tile Deleted"));
                    refreshlist();
                }).$promise;
            }
        };

        $scope.toggleEdit = function (tile) {
            if (angular.equals({}, tile)) {
                if ($scope.isDirty()) {
                    var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                    if (!answer) {
                        return false;
                    }
                }
                $scope.makeClean();
            }
            $scope.editTile = angular.copy(tile);
            $scope.tmpImage = $scope.editTile.icon;

            $scope.showEdit = !$scope.showEdit;
            if (!$scope.showEdit)
                resetQueryString();
        };
        
        $scope.hidetoggle = function (tile, tileType) {
            if ($scope.working)
                return;
            $scope.working = true;

            if (tileType == 'teacher') {
                tile.hidden = !tile.hidden;
            }
            else if (tileType == 'student') {
                tile.teacher_tile = !tile.teacher_tile;
            }
            $scope.tileItemsPromise = Tiles.toggle(tile, function () {
                $scope.working = false;
                if (tileType == 'teacher') {
                    toaster.pop('success', tile.hidden ? gettext("Hidden from All Users") : gettext("Visible to All Users"));
                }
                else if (tileType == 'student') {
                    toaster.pop('success', tile.teacher_tile ? gettext("Hidden from Students") : gettext("Visible to Students"));
                }
            }).$promise.then(function () { $scope.working = false; });
        };

        $scope.isDuplicateTitle = function (tile, title, form) {
            var existing = false;
            if (title) {
                var sanitized = title.toUpperCase();
                var existing = _.find($scope.tiles, function (t) { return t.title.toUpperCase() === sanitized && t.id !== tile.id; });
                existing = angular.isDefined(existing);
            }
            if (form) form.title.$setValidity('custom', !existing);

            return existing;
        }

        $scope.isDuplicateExisting = function (title) {
            return false
        }

        $scope.isDuplicateSelected = function (title) {
            return false;
        }
        $scope.submitUSB = function () {
            $scope.uploadClicked = true;
            $scope.working = true;
            //$('.uploadcomplete-false').css('display', 'block');
            console.log($scope.actual_files);

            var index = 0; //temp

            var formobj = {};
            formobj.title = ''; //add the updated title
            formobj.selected = [$scope.actual_files[index]];
            formobj.microsite = true;

            $scope.usbUploadPromise = USB.uploadContent(formobj, function (response) {
                if (response['result'] == 'success' && response['micrositeURL']) {
                    toaster.pop('success', gettext("Item(s) successfully uploaded"));
                    $scope.working = false;
                    $scope.newTile.url_string = response['micrositeURL'];
                    $scope.newTile.storage_folder = response['storageLocation'];

                    $scope._form_url = true;
                    $scope._form_usb = false;
                    $scope._form_upload_complete = true;

                    $('#usb_container_tile').remove();
                }
                else if (response.type && (response.type == 'usb_removed' || response.type === 'out_of_space')) {
                    var msg = response.type === 'out_of_space' ? gettext("There is not enough space on the internal drive.  Please connect external drive and retry.") : gettext("There was a problem with the USB device");
                    toaster.pop('error', msg);
                    //clean stuff up
                    //console.log(response.type);
                }
            }).$promise;            
        }

        $scope.tree_dirty = false;
        $scope.tree_valid = false;
        $scope.actual_files = [];

        $scope.onFileSelect = function () {

            $scope.tree_dirty = true;
            $scope.tree_valid = false;

            $scope.fileErrors = [];

            $scope.actual_files = [];

            var selected_id_list = $.jstree.reference('#tile_usb_browser').get_selected();
            $scope.tree_ready = (selected_id_list.length > 0) ? true : false;

            var tmp = [];
            //create a mapping for each file id to new title.
            for (var i = 0; i < selected_id_list.length; i++) {
                var elm = $.jstree.reference('#tile_usb_browser').get_json(selected_id_list[i]);
                //only add if file
                if (elm.icon == 'jstree-file') {
                    $scope.tree_valid = true;
                    $scope.actual_files.push(selected_id_list[i]);
                }
            }
            //$scope.file_title_mapping = tmp;
            $scope.$apply();
        };

        $scope.onIconSelect = function ($files) {

            $scope.iconMaxSizeError = undefined;
            $scope.iconTypeError = undefined;

            var file = $files[0];
            if (FIELD_VAL.tileIconMax < file.size) {
                $scope.iconMaxSizeError = interpolate(gettext("%(filename)s : The maximum size of a file is %(maxsize)s."), { filename: file.name, maxsize: $filter('filesizeformat')(FIELD_VAL.tileIconMax) }, true);
                return;
            }

            if (file.type.indexOf('image') !== 0)
            {
                $scope.iconTypeError = interpolate(gettext("%(filename)s : Only images can be used for icons."), { filename: file.name }, true);
                return;
            } 

            $scope.icon_file.push(file);
            var reader = new FileReader();

            reader.onload = function (e) {
                $scope.$apply(function () {
                    $scope.tmpImage = e.target.result;
                });
            }

            reader.readAsDataURL(file);

        };
        //reset the file list on each click as reselecting same file again wont trigger 'fileSelected'
        $scope.clearFileSelection = function ($event) {
            $event.target.value = '';
            $scope.icon_file = [];
            $scope.iconMaxSizeError = '';
            $scope.iconTypeError = '';
            $scope.tmpImage = '';
        };

        $scope.checkEState = function()
        {
            var b = (
                $scope.editTile.title == '' ||
                $scope.editTile.url_string == '' ||
                $scope.editTileForm.title.$error.custom ||
                $scope.editTileForm.title.$error.required ||
                $scope.editTileForm.edit_url.$error.required ||
                ($scope.icon_file.length === 0 && $scope.tmpImage == '')
            );
            //console.log('b: ' + b);
            return b;

        }

        $scope.isAnythingSelected = function () {
            var selected_id_list = $.jstree.reference('#tile_usb_browser').get_selected();
            if (selected_id_list.length > 0) {
                $.jstree.reference('#tile_usb_browser').deselect_all()
            }
            return false;
        }


    }]);

}());