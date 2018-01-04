/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    angular.module('ecControllers').controller("PreloadUsbCtrl", ["$scope", "$location", "$route", 'USB', 'toaster', 'Packages', 'USB2',
        function ($scope, $location, $route, USB, toaster, Packages, USB2) {
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
            $scope.stopAllUploadPolls = false;
            $scope.uploadClicked = false;
            $scope.cancellable = false;
            $scope.reload_disabled = true;

            $scope.packageNames = [];
            Packages.query(function (response) {
                _.each(response, function (r) {
                    $scope.packageNames.push({
                        'id': r.id,
                        'name': r.title
                    });
                });
            });

            $scope.backButtonClick = function () {
                $location.path('/');
            };

            $scope.reload_page = function () {
                $('#usb_browser').remove();
                $route.reload();
            }

            $scope.$on('$destroy', function () {
                $(window).off('beforeunload');
            });

            $(window).on('beforeunload', function (e) {
                if ($scope.tree_dirty) {
                    //var message = gettext('If you leave this page all unsaved changes will be lost, are you sure?');
                    var message = gettext('If a package was successfully transferred, it will be added to the database in the background.');
                    e.returnValue = message;
                    return message;
                }
            });
            $scope.$on('$locationChangeStart', function (event) {
                if (!$scope.tree_dirty) return;
                //var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                var answer = confirm(gettext('If a package was successfully transferred, it will be added to the database in the background.\n\nAre you sure you want to leave this page?'));
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

            $scope.isDuplicateExisting = function (title) {
                var exists = false;
                _.filter($scope.packageNames, function (item) {
                    if (item.name == title) {
                        exists = true;
                    }
                });
                return exists;
            }

            $scope.isDuplicateSelected = function (title) {
                var selected_id_list = $.jstree.reference('#usb_browser').get_selected();
                for (var i = 0; i < selected_id_list.length; i++) {
                    var elm = $.jstree.reference('#usb_browser').get_json(selected_id_list[i]);
                    if (elm.text == title) {
                        toaster.pop('warn', gettext("A package with this name is already selected, remove the other selection to continue"));
                        return true;
                    }
                }
                return false;
            }


            /*
            *   Cancel Logic
            */
            $scope.cancel1disabled = function (index) {
                if (!$scope.uploadClicked) {
                    return false;
                }
                else {
                    var idx = $scope.getQueueIndex();
                    return (index <= idx) || $scope.file_title_mapping[index].uploaded
                }
            }
            $scope.current_request = null;
            $scope.cancelUpload = function (file_id) {
                // untick in the usb tree
                var selected_id_list = $.jstree.reference('#usb_browser').get_selected();
                for (var i = 0; i < selected_id_list.length; i++) {
                    var elm = $.jstree.reference('#usb_browser').get_json(selected_id_list[i]);
                    if ($scope.file_title_mapping[file_id].path == elm.id) {
                        $.jstree.reference('#usb_browser').deselect_node(elm);
                    }
                }
                // now remove all references to it
                $scope.file_title_mapping.splice(file_id, 1);
                $scope.actual_files.splice(file_id, 1);
                $scope.cancelTracker.splice(file_id, 1);
            }
            $scope.cancelUploadPost = function (file_id) {
                $scope.current_request.cancel("Cancelled");
                $scope.file_title_mapping[file_id].inprocess_prefix = gettext('Cancelled')
                //$scope.file_title_mapping[file_id].inprocess_status = gettext('Cancelled');
                $scope.file_title_mapping[file_id].warning = true;
                $scope.file_title_mapping[file_id].uploaded = true;
            }
            $scope.cancel2disabled = function (index) {
                return $scope.uploadQueue[index] === undefined ? true : ($scope.uploadQueue[index] && !$scope.file_title_mapping[index].uploaded);
                //return !$scope.cancellable;
            }

            /*
            *   State tracking logic
            */
            $scope.uploadQueue = [];
            $scope.cancelTracker = [];
            $scope.getQueueIndex = function () {
                var i;
                for (i = 0; i < $scope.uploadQueue.length; i++) {
                    if (!$scope.uploadQueue[i]) {
                        return i;
                    }
                }
                return i + 1;
            }
            $scope.incrementQueue = function () {
                $scope.uploadQueue[$scope.getQueueIndex()] = true;
                $scope.singleUpload();
            }
            $scope.currentdownload = null;
            $scope.isCancelable = function (index) {
                return $scope.cancelTracker[index];
            }
            $scope.resetCancelTracker = function () {
                for (var i = 0; i < $scope.cancelTracker.length; i++)
                    $scope.cancelTracker[i] = false;
            }

            $scope.checkAllComplete = function () {
                var alldone = true;
                _.each($scope.file_title_mapping, function (f) {
                    if (!f.uploaded)
                        alldone = false;
                });
                if (alldone) {
                    $scope.stopAllUploadPolls = true;
                    $scope.working = false;
                    $scope.$location.path('/');
                    $scope.$destroy(); //call destroy to unbind the dirty bit
                }
            }

            //only enable upload when there is at least one thing valid to upload. i.e. not existing or existing and checked
            $scope.valid_upload_exists = function () {
                var validuploadexists = false;
                _.filter($scope.file_title_mapping, function (item) {
                    if (!item.exists || (item.exists && item.overwriteConfirmed)) {
                        validuploadexists = true;
                    }
                });
                return validuploadexists;
            }

            $scope.onFileSelect = function () {
                $scope.tree_dirty = true;
                $scope.file_title_mapping = [];
                $scope.fileErrors = [];
                $scope.actual_files = [];
                /*
                var exists = false;
                _.filter($scope.packageNames, function (item) {
                    if (item.name == $files[i].name) {
                        exists = true;
                    }
                });
                */
                var selected_id_list = $.jstree.reference('#usb_browser').get_selected();
                $scope.tree_ready = (selected_id_list.length > 0) ? true : false;

                var tmp = []
                //create a mapping for each file id to new title.
                for (var i = 0; i < selected_id_list.length; i++) {
                    var elm = $.jstree.reference('#usb_browser').get_json(selected_id_list[i]);

                    var exists = $scope.isDuplicateExisting(elm.text);

                    //only add if file
                    if (elm.icon == 'jstree-file') {
                        $scope.actual_files.push(selected_id_list[i]);
                        var title = elm.text.substr(0, elm.text.lastIndexOf("."));
                        tmp.push({
                            'file_index': i,
                            'filename': elm.text,
                            'title': title,
                            'path': selected_id_list[i],
                            'inprocess_prefix': gettext('Pending'),
                            //'inprocess_status': gettext('Pending'),
                            'upload_total': elm.filesize,
                            'uploaded': false,
                            'error': false,
                            'warning': false,
                            'exists': exists,
                            'overwriteConfirmed': false,
                            'cancelled': false,
                            'current': false //spinner control
                        });
                    }
                }
                $scope.file_title_mapping = tmp;
                $scope.$apply();
            };

            $scope.task_states = [
               'PENDING',
               'UNZIPPING',
               'IMPORTING',
               'SUCCESS',
               'FAIL',
               'COPYING'
            ];

            $scope.pollProcessState = function (task_id) {
                $.ajax({
                    url: "/rest/poll_state/?",
                    type: "POST",
                    data: "task_id=" + task_id,
                }).done(function (task) {
                    if (task.state) {
                        //console.log(task.state + ' @@@ ' + task_id);
                        if (task.state == $scope.task_states[1]) { //UNZIPPING
                            $scope.$apply(function () {
                                if (task.meta && task.meta.unzip_percent) {
                                    _.find($scope.file_title_mapping, function (map) {
                                        if (task_id == map.importJobID) {
                                            map.inprocess_prefix = gettext('Unzipping ') + task.meta.unzip_percent;
                                        }
                                    });
                                }
                            });
                        }
                        else if (task.state == $scope.task_states[2]) { //IMPORTING
                            $scope.$apply(function () {
                                if (task.meta && task.meta.import_percent) {
                                    //console.log(task.meta);
                                    _.find($scope.file_title_mapping, function (map) {
                                        if (task_id == map.importJobID) {
                                            map.inprocess_prefix = gettext('Adding to database');
                                        }
                                    });
                                }
                            });
                        }
                        else if (task.state == $scope.task_states[3]) { //SUCCESS / COMPLETE
                            $scope.$apply(function () {
                                _.find($scope.file_title_mapping, function (map) {
                                    if (task_id == map.importJobID) {
                                        map.inprocess_prefix = gettext('Success');
                                        map.uploaded = true;
                                        toaster.pop('success', gettext("Item successfully imported"));
                                        //check if all complete
                                        $scope.checkAllComplete();
                                    }
                                });
                            });
                        }
                        else if (task.state == 'FAILURE') {
                            $scope.$apply(function () {
                                if (task.meta && task.meta == 'empty_package') {
                                    _.find($scope.file_title_mapping, function (map) {
                                        if (task_id == map.importJobID) {
                                            map.inprocess_prefix = gettext('Failed');
                                            map.warning = true;
                                            map.uploaded = true;
                                            toaster.pop('error', gettext("Invalid package"));
                                            //check if all complete
                                            $scope.checkAllComplete();
                                        }
                                    });
                                }
                            });
                            //$scope.checkAllComplete();
                        }


                    }
                    /*
                    $scope.$apply();
                    */

                    // create the infinite loop of Ajax calls to check the state
                    // of the current task unless its success or fail
                    if (task.state == 'SUCCESS' || task.state == 'FAILURE') {
                        //wrap up scope
                        $scope.incrementQueue();
                    } else {
                        $scope.pollProcessState(task_id);
                    }
                });
            }

            /*
            *   Upload the first incomplete file in the current queue
            */
            $scope.singleUpload = function () {
                $scope.checkAllComplete();

                var index = $scope.getQueueIndex();
                if (index < $scope.uploadQueue.length) {
                    var single_file = $scope.actual_files[index];

                    var packagesDeleteId = [];
                    _.filter($scope.packageNames, function (item) {
                        var map = $scope.file_title_mapping[index];
                        if (item.name == map.filename) {
                            if (map.exists && map.overwriteConfirmed) {
                                packagesDeleteId.push(item.id);
                            }
                        }
                    });

                    if (single_file != null) {
                        Packages.bulkdelete({ 'ids': packagesDeleteId }, function () {
                            var formobj = {};
                            formobj.title = $scope.file_title_mapping[index].path; //add the updated title
                            formobj.selected = [$scope.file_title_mapping[index].path];
                            formobj.async = 'true'
                            formobj.x_progress_id = index;


                            var approved = true;

                            _.find($scope.file_title_mapping, function (map) {
                                if (single_file == map.path) {
                                    if (map.exists && !map.overwriteConfirmed) {
                                        approved = false;
                                        map.cancelled = true;
                                        map.error = true;
                                        map.uploaded = true;
                                    }
                                    map.current = true; //show the spinner for current only
                                    map.inprocess_prefix = gettext('Copying');
                                }
                            });
                            //do an initial complete check, incase nothing was approved
                            $scope.checkAllComplete();
                            if (approved) {
                                $scope.usbUploadPromise = USB.uploadContent(formobj, function (response) {
                                    if (response['result'] == 'success' && ('importJobID' in response && response['importJobID'] != '')) {
                                        _.find($scope.file_title_mapping, function (map) {
                                            if (single_file == map.path) {
                                                if ('importJobID' in response) {
                                                    var importJobID = response['importJobID'];
                                                    map.importJobID = importJobID;
                                                    //map.inprocess_prefix = 'Copying';
                                                    //map.inprocess_status = '';
                                                    $scope.pollProcessState(importJobID);
                                                }
                                            }
                                        });
                                    }
                                    else {
                                        if (response.type && (response.type == 'usb_removed' || response.type === 'out_of_space')) {
                                            $('#usb_browser').empty();
                                            $scope.file_title_mapping = [];
                                            $scope.stopAllUploadPolls = true;
                                            var msg = response.type === 'out_of_space' ? gettext("There is not enough space on the internal drive.  Please connect external drive and retry.") : gettext("There was a problem with the USB device");
                                            toaster.pop('error', msg);
                                            $scope.working = false;
                                            $scope.tree_ready = false;
                                        }

                                        _.find($scope.file_title_mapping, function (map) {
                                            if (single_file == map.path) {
                                                toaster.pop('error', gettext('A file error occurred'));
                                                map.cancelled = true;
                                                map.warning = true;
                                                map.uploaded = true;
                                            }
                                        });
                                        $scope.checkAllComplete();
                                        $scope.incrementQueue();
                                    }
                                }).$promise;
                            }//end if approved
                            else {
                                $scope.incrementQueue();
                            }
                        });//end bulkdelete
                    }//end if singlefile
                }
            }

            $scope.submitUSB = function () {
                $scope.uploadClicked = true;
                $scope.stopAllUploadPolls = false;
                $scope.working = true;
                $('.uploadcomplete-false').css('display', 'block');

                for (var i = 0; i < $scope.file_title_mapping.length; i++) {
                    $scope.uploadQueue.push(false);
                    $scope.cancelTracker.push(false);
                }
                $scope.singleUpload();

            }

        }]);

}());