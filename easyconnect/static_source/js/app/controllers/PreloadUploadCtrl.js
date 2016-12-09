/// <reference path="../../angularjs/angular.js" />
/// <reference path="../underscore-min.js" />
(function () {
    'use strict';

    angular.module('ecControllers').controller("PreloadUploadCtrl", ["$scope", "$location", 'Packages', 'toaster', 'FIELD_VAL', '$routeParams', '$filter', '$q', 'Packages2',
        function ($scope, $location, Packages, toaster, FIELD_VAL, $routeParams, $filter, $q, Packages2) {
            $scope.preloaded = true;
            $scope.FIELD_VAL = FIELD_VAL;
            $scope.content = {};
            $scope.working = false;
            $scope.file_title_mapping = [];
            $scope.actual_files = [];
            $scope.fileErrors = [];
            $scope.packageNames = [];
            $scope.stopAllUploadPolls = false;
            $scope.uploadClicked = false;
            $scope.cancellable = false;

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

            $scope.$on('$destroy', function () {
                $(window).off('beforeunload');
            });

            $(window).on('beforeunload', function (e) {
                if ($scope.uploadForm.$dirty) {
                    //var message = gettext('If you leave this page all unsaved changes will be lost, are you sure?');
                    var message = gettext('If a package was successfully transferred, it will be added to the database in the background.');
                    e.returnValue = message;
                    return message;
                }
            });

            $scope.$on('$locationChangeStart', function (event) {
                if (!$scope.uploadForm.$dirty) return;
                //var answer = confirm(gettext('If you leave this page all unsaved changes will be lost, are you sure?'))
                //var answer = confirm(gettext('Are you sure you want to leave this page?\n\nNote: if the upload has completed then the add to database process will continue in the background.'))
                var answer = confirm(gettext('If a package was successfully transferred, it will be added to the database in the background.\n\nAre you sure you want to leave this page?'));

                if (!answer) {
                    event.preventDefault();
                }
            });

            //reset the file list on each click as reselecting same file again wont trigger 'fileSelected'
            $scope.clearFileSelection = function ($event) {

                $("#clone-me").closest('form').trigger('reset');

                $event.target.value = '';
                $scope.actual_files = [];
                $scope.file_title_mapping = [];
            };

            $scope.pollUploadStatus = function (index, progressID) {
                if (!$scope.stopAllUploadPolls) {
                    $.ajax({
                        url: '/rest/pollupload/?',
                        type: 'post',
                        headers: {
                            "X-Progress-ID": progressID,
                        },
                        dataType: 'json',
                        success: function (data) {
                            var cancelled = false;
                            if (data != null) {
                                if (data.cancelled) {
                                    cancelled = true;
                                }
                                else {
                                    var percentageComplete = Math.floor(data.uploaded / $scope.file_title_mapping[index].upload_total * 100) + ' %';
                                    $scope.file_title_mapping[index].inprocess_prefix = gettext('Uploading ') + percentageComplete;
                                    //reset these in case a cancel has been attempted and failed
                                    $scope.file_title_mapping[index].warning = false;
                                    $scope.file_title_mapping[index].uploaded = false;
                                }
                            }
                            
                            $scope.$apply();
                            if ($scope.file_title_mapping[index]) {
                                if (!cancelled) {
                                    if (!$scope.file_title_mapping[index].upload_completed) {
                                        setTimeout(function () {
                                            $scope.pollUploadStatus(index, progressID)
                                        }, 200);
                                    }
                                }
                            }
                        }
                    });
                }
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
                //var secondary_condidtion = $scope.uploadQueue[index] === undefined ? true : ($scope.uploadQueue[index] && (!$scope.file_title_mapping[index].uploaded));
                //return secondary_condidtion || $scope.uploadClicked;
            }
            $scope.current_request = null;
            $scope.cancelUpload = function (file_id) {
                //if (!$scope.uploadClicked) {
                    $scope.file_title_mapping.splice(file_id, 1);
                    $scope.actual_files.splice(file_id, 1);
                    $scope.cancelTracker.splice(file_id, 1);
                //}
            }
            $scope.cancelUploadPost = function (file_id) {
                var guid = $scope.file_title_mapping[file_id].guid
                $.ajax({
                    url: "/rest/cancelupload/?",
                    type: 'post',
                    headers: {
                        "X-Progress-ID": guid,
                    },
                    dataType: 'json',
                    success: function (data) {}
                });
                //$scope.current_request.cancel("Cancelled");
                $scope.file_title_mapping[file_id].inprocess_prefix = gettext('Contacting server, attempting to cancel.');
                $scope.file_title_mapping[file_id].warning = true;
                $scope.file_title_mapping[file_id].uploaded = true;
            }
            $scope.cancel2disabled = function (index) {
                return $scope.uploadQueue[index] === undefined ? true : ($scope.uploadQueue[index] && !$scope.file_title_mapping[index].uploaded);
            }

            /*
            *   State tracking logic
            */
            $scope.uploadQueue = [];
            $scope.cancelTracker = [];
            $scope.getQueueIndex = function () {
                if ($scope.uploadQueue.length > 0) {
                    var i;
                    for (i = 0; i < $scope.uploadQueue.length; i++) {
                        if (!$scope.uploadQueue[i]) {
                            return i;
                        }
                    }
                    return i + 1;
                }
                else {
                    return 0;
                }
            }
            $scope.incrementQueue = function () {
                $scope.uploadQueue[$scope.getQueueIndex()] = true;
                $scope.singleUpload();
            }
            $scope.isCancelable = function (index) {
                return $scope.cancelTracker[index];
            }
            $scope.resetCancelTracker = function () {
                for (var i = 0; i < $scope.cancelTracker.length; i++)
                    $scope.cancelTracker[i] = false;
            }


            /*
            *   Check for finish and wrap up scope
            */
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

            $scope.onFileSelect = function ($files) {

                $scope.file_title_mapping = [];
                $scope.fileErrors = [];

                $scope.stopAllUploadPolls = true;

                $scope.atleastonevalid = false;

                //create a mapping for each fileobject, to new title.
                for (var i = 0; i < $files.length; i++) {
                    var exists = false;
                    _.filter($scope.packageNames, function (item) {
                        if (item.name == $files[i].name) {
                            exists = true;
                        }
                    });

                    if ($files[i].name.length > FIELD_VAL.filenameMax) {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum length of the filename is %(maxchars)s."), { filename: $files[i].name, maxchars: FIELD_VAL.filenameMax }, true));
                    } else if ($files[i].size > FIELD_VAL.fileSizeMax) {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : The maximum size of a file is %(maxsize)s."), { filename: $files[i].name, maxsize: $filter('filesizeformat')(FIELD_VAL.fileSizeMax) }, true));
                    } else if ($files[i].name.toLowerCase().split('.').pop() !== 'zip') {
                        $scope.fileErrors.push(interpolate(gettext("%(filename)s : Only ZIP files are allowed"), { filename: $files[i].name }, true));
                    } else {
                        $scope.actual_files.push($files[i]);
                        var title = $files[i].name.substr(0, $files[i].name.lastIndexOf("."));;
                        $scope.file_title_mapping.push({
                            'file_index': i,
                            'filename': $files[i].name,
                            'title': title,
                            'inprocess_prefix': gettext('Pending'),
                            //'inprocess_status': gettext('Pending'),
                            'upload_total': $files[i].size,
                            'uploaded': false,
                            'error': false,
                            'warning': false,
                            'exists': exists,
                            'overwriteConfirmed': false,
                            'cancelled': false,
                            'current': false,
                            'guid': $scope.generateGuid()
                        });
                    }
                }
                $scope.uploadForm.$setDirty();
            };
            
            $scope.task_states = [
                'PENDING',
                'UNZIPPING',
                'IMPORTING',
                'SUCCESS',
                'FAIL'
            ];

            $scope.pollProcessState = function (task_id) {
                $.ajax({
                    url: "/rest/poll_state/?",
                    type: "POST",
                    data: "task_id=" + task_id,
                }).done(function (task) {
                    if (task.state) {
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
                                            map.inprocess_prefix = gettext('Adding to database')
                                            //map.inprocess_status = task.meta.import_percent;
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
                                        //map.inprocess_status = gettext('Success');
                                        map.uploaded = true;
                                        toaster.pop('success', gettext("Item successfully uploaded"));
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
                                            map.inprocess_prefix = gettext('Failed')
                                            //map.inprocess_status = gettext('Invalid package');
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
                            formobj.file = single_file;
                            formobj.x_progress_id = $scope.file_title_mapping[index].guid;

                            var approved = true;

                            _.find($scope.file_title_mapping, function (map) {
                                if (single_file.name == map.filename) {
                                    if (map.exists && !map.overwriteConfirmed) {
                                        approved = false;
                                        map.cancelled = true;
                                        map.error = true;
                                        map.uploaded = true;
                                    }
                                    map.current = true; //will show spinner
                                    map.inprocess_status = gettext('Uploading');
                                }
                            });
                            //do an initial complete check, incase nothing was approved
                            $scope.checkAllComplete();
                            if (approved) {
                                $scope.pollUploadStatus(index, $scope.file_title_mapping[index].guid);

                                //Packages.save(formobj, function (success) {
                                $scope.cancelTracker[index] = true;
                                $scope.current_request = Packages2.cancellable_method(formobj);
                                $scope.current_request.promise.then(function (success) {
                                    $scope.resetCancelTracker();
                                    // on error
                                    if (success && success.data)
                                        success = success.data;
                                    if (success['file_error'] || ('importJobID' in success && success['importJobID'] == '')) {
                                        toaster.pop('error', gettext('A file error occurred'));
                                        _.find($scope.file_title_mapping, function (map) {
                                            if (single_file.name == map.filename) {
                                                map.cancelled = true;
                                                map.warning = true;
                                                map.uploaded = true;
                                            }
                                        });
                                        $scope.checkAllComplete();
                                        $scope.incrementQueue();
                                    }
                                    else if (success['cancelled']) {
                                        _.find($scope.file_title_mapping, function (map) {
                                            if (single_file.name == map.filename) {
                                                map.cancelled = true;
                                                map.warning = true;
                                                map.uploaded = true;
                                            }
                                        });
                                        $scope.checkAllComplete();
                                        $scope.incrementQueue();
                                    }
                                    else { // on success
                                        _.find($scope.file_title_mapping, function (map) {
                                            if (single_file.name == map.filename) {
                                                map.inprocess_prefix = gettext("Uploading ") + '100%'; // as it will probably be stuck on 90-something%
                                                map.importJobID = success.importJobID;
                                                map.upload_completed = true; //for the poll process state only
                                                map.warning = false; // clear this in case a cancel has been attempted and failed
                                                map.uploaded = false; // clear this in case a cancel has been attempted and failed
                                                $scope.pollProcessState(success.importJobID);
                                            }
                                        });
                                    }
                                }, function (fail) { // general failure
                                    $scope.resetCancelTracker();
                                    _.find($scope.file_title_mapping, function (map) {
                                        if (single_file.name == map.filename) {
                                            map.error = true;
                                            map.uploaded = true;
                                            map.inprocess_prefix = gettext('Failed');
                                        }
                                    });
                                    $scope.checkAllComplete();
                                    $scope.incrementQueue();
                                });

                            }//end if approved
                            else {
                                $scope.incrementQueue();
                            }

                        });//end bulkdelete
                    }//end if single_file

                }
            }
            
            $scope.save = function (metadata, category) {
                $scope.uploadClicked = true;
                $scope.stopAllUploadPolls = false;
                $scope.working = true;
                $('.uploadcomplete-false').css('display', 'block');
                //var total_count = $scope.actual_files.length;

                for (var i = 0; i < $scope.file_title_mapping.length; i++) {
                    $scope.uploadQueue.push(false);
                    $scope.cancelTracker.push(false);
                }
                $scope.singleUpload();
            };

            $scope.generateGuid = function() {
                var result, i, j;
                result = '';
                for(j=0; j<32; j++) {
                    //if( j == 8 || j == 12|| j == 16|| j == 20) 
                        //result = result + '-';
                    i = Math.floor(Math.random()*16).toString(16).toUpperCase();
                    result = result + i;
                }
                return result;
            }

        }]);

}());