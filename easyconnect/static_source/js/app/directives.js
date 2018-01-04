/// <reference path="../../angularjs/angular.js" />
(function () {
    angular.module("ecDirectives", []).directive('lessons', function () {
        return {
            restrict: 'A',
            templateUrl: '/angularpartials/lessons.html'
        }
    }).directive('contentitems', function () {
        return {
            restrict: 'A',
            templateUrl: '/angularpartials/contentitems.html',
            controller: ['$scope', 'ContentItems', 'toaster', '$rootScope', 'APP_EVENTS', '$location', 'userService', 'SharedData',
                function ($scope, ContentItems, toaster, $rootScope, APP_EVENTS, $location, userService, SharedData) {

                $scope.working = false;
                $scope.$location = $location;
                $scope.user = userService.get();
                $scope.checkedItems = [];
                $scope.expanded = [];

                $scope.featuretoggle = function (item) {
                    if ($scope.working)
                        return;
                    $scope.working = true;
                    item.featured = !item.featured;
                    $scope.contentItemsPromise = ContentItems.update(item, function () {
                        $rootScope.$broadcast(APP_EVENTS.featuredContentChanged);
                        toaster.pop('success', item.featured ? gettext("Featured") : gettext("Unfeatured"));
                    }).$promise.then(function () { $scope.working = false; });
                };

                $scope.hidetoggle = function (item) {
                    if ($scope.working)
                        return;
                    $scope.working = true;
                    item.hidden = !item.hidden;
                    $scope.contentItemsPromise = ContentItems.update(item, function () {
                        $scope.working = false;
                        toaster.pop('success', item.hidden ? gettext("Hidden") : gettext("Visible"));
                    }).$promise.then(function () { $scope.working = false; });
                };

                $scope.expandtoggle = function (item) {
                    var pos = $scope.expanded.indexOf(item.id);
                    if (pos > -1) {
                        $scope.expanded.splice(pos, 1);
                    } else {
                        $scope.expanded.push(item.id);
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
                    $rootScope.$broadcast(APP_EVENTS.checkedItemsChanged);
                };

                $scope.$on(APP_EVENTS.clearCheckedItems, function () {
                    $scope.checkedItems = SharedData.checkedContentItems = [];
                });
            }],
            scope: {
                contentitems: "=",
                lesson: "=",
                checkedItems: "="
            }
        }
    }).directive('sidebar', function () {
        return {
            restrict: 'A',
            templateUrl: '/angularviews/sidebar.html'
        }
    }).directive('tagcloud', function () {
        return {
            controller:"TagCtrl",
            restrict: 'A',
            templateUrl: '/angularpartials/tagcloud.html',
            transclude: true,
            scope: {
                tags: "=?",
                onclick: "="
            }
        }
    }).directive('sort', ['$location', function ($location) {
        return {
            restrict: 'A',
            required:'sort',
            templateUrl: '/angularpartials/sort.html',
            scope: {
                sort: "=",
                titlekey: "@?",
                datekey: "@?"
            },
            link: function (scope, element, attrs) {

            },
            controller: function ($scope, $location) {

                $scope.titlekey = $scope.titlekey || 'title';
                $scope.datekey = $scope.datekey || 'date_added';

                $scope.sortActive = function (sortby) {
                    var params = $location.search();
                    return params.ordering && params.ordering.indexOf(sortby) > -1;
                }
            }
        }
    }]).directive('pager', ['$location', function ($location) {
        return {
            restrict: 'AE',
            templateUrl: '/angularpartials/pager.html',
            scope: {
                model: "=",
                pagefn: "="
            }
        };
    }]).directive('categoryselect', function () {
        return {
            restrict: 'A',
            templateUrl: '/angularpartials/categoryselect.html',
            controller: 'CategoryCtrl',
            scope: {
                categoryselect: "="
            }
        }
    }).directive('focusMe', function($timeout, $parse) {
        return {
            link: function(scope, element, attrs) {
                var model = $parse(attrs.focusMe);
                scope.$watch(model, function(value) {
                    if(value === true) { 
                        $timeout(function() {
                            element[0].focus(); 
                        });
                    }
                });
                // set attribute value to 'false' on blur event:
                element.bind('blur', function() {
                    //console.log('blur');
                    try{
                        scope.$apply(model.assign(scope, false));
                    } catch (ex) {
                    }
                });
            }
        };
    }).directive('focusOn', function ($timeout, $parse) {
        return {
            link: function (scope, element, attrs) {
                var model = $parse(attrs.focusOn);
                scope.$watch(model, function (value) {
                    if (value === true) {
                        $timeout(function () {
                            element[0].focus();
                        });
                    }
                });
            }
        };
    })/*.directive('fileUpload', function () {
        return {
            require: 'ngModel',
            scope: true,        //create a new scope
            link: function (scope, el, attrs, ngModel) {
                var firstload = true;
                ngModel.$render = function () {
                    if (!firstload)
                        ngModel.$setViewValue(el.val());
                    else
                        firstload = false;
                };

                el.bind('change', function (event) {
                    ngModel.$render();
                    var files = event.target.files;
                    //iterate files since 'multiple' may be specified on the element
                    for (var i = 0;i<files.length;i++) {
                        //emit event upward
                        scope.$emit("fileSelected", { file: files[i] });
                    }
                });


            }
        };
    })*/.directive("categorytree", function (RecursionHelper) {
        return {
            restrict: "AE",
            scope: {
                current: "=",
                parent: "=",
                level: "=",
                save: "=",
                remove: "=",
                addCategory: "=",
                cancel: "=",
                validate: "="
            },
            templateUrl: '/angularpartials/categorytree.html',
            compile: function (element) {
                return RecursionHelper.compile(element, function (scope, iElement, iAttrs, controller, transcludeFn) {
                    // Define your normal link function here.
                    // Alternative: instead of passing a function,
                    // you can also pass an object with 
                    // a 'pre'- and 'post'-link function.
                });
            }
        };
    }).directive("usbtree", function (RecursionHelper) {
        return {
            restrict: "AE",
            link: function (scope, element, attrs) {
                
                //jstree conditional select node
                (function ($, undefined) {
                    "use strict";
                    $.jstree.defaults.conditionalselect = function () { return true; };
                    $.jstree.plugins.conditionalselect = function (options, parent) {
                        this.select_node = function (obj, supress_event, prevent_open, evt) {
                            var jstree_event_type = 'select_node';
                            if (this.settings.conditionalselect.call(this, this.get_node(obj), jstree_event_type)) {
                                parent.select_node.call(this, obj, supress_event, prevent_open);
                                if (this.settings.shouldselectparent.call(this, this.get_node(obj), jstree_event_type)) {
                                    parent.select_node.call(this, this.get_node(obj).parent, supress_event, prevent_open);
                                }
                            }
                            this.settings.dofileselect.call(this, evt);
                        };
                        this.deselect_node = function (obj, supress_event, prevent_open, evt) {
                            var jstree_event_type = 'deselect_node';
                            if (this.settings.conditionalselect.call(this, this.get_node(obj), jstree_event_type)) {
                                parent.deselect_node.call(this, obj, supress_event, prevent_open);
                                //clear the parent
                                if ($(element).jstree('is_leaf', this.get_node(obj))) {
                                    parent.deselect_node.call(this, this.get_node(obj).parent, supress_event, prevent_open);
                                }
                            }
                            this.settings.dofileselect.call(this, evt);
                        };
                    };
                })(jQuery);


                $(element).jstree({
                    'dofileselect': function (evt) {
                        if (evt) {
                            //console.log('user interaction');
                            scope.onFileSelect();
                        }
                        else {
                            //console.log('...other');
                        }
                    },
                    'shouldselectparent': function (node, event_type) {
                        var node_array = [];
                        var select_parent = true;

                        if (node && $(element).jstree('is_leaf', node)) {
                            //check all siblings to see if we should check or uncheck the parent
                            if (node.parent) {
                                var group_parent = $.jstree.reference(element).get_json(node.parent);
                                if (group_parent.children.length > 0) {
                                    if (event_type == 'select_node' && $(element).jstree('is_leaf', node)) {
                                        var i = 0;
                                        for (i = 0; i < group_parent.children.length; i++) {
                                            if (group_parent.children[i].id != node.id) { //only check siblings not self
                                                if (!group_parent.children[i].state['selected'] && $(element).jstree('is_leaf', group_parent.children[i])) { //if any others are not selected
                                                    select_parent = false;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        else {
                            select_parent = false;
                        }
                        return select_parent;
                    },
                    'canclearparent': function (node, event_type) {
                        var node_array = [];
                        var can_clear_parent = true;
                        
                        if (node && $(element).jstree('is_leaf', node)) {
                            //check all siblings to see if we should check or uncheck the parent
                            if (node.parent) {
                                var group_parent = $.jstree.reference(element).get_json(node.parent);
                                if (group_parent.children.length > 0) {
                                    if (event_type == 'deselect_node' && $(element).jstree('is_leaf', node)) {
                                        var i = 0;
                                        for (i = 0; i < group_parent.children.length; i++) {
                                            if (group_parent.children[i].id != node.id && $(element).jstree('is_leaf', group_parent.children[i])) { //only check sibling leaves
                                                if (group_parent.children[i].state['selected']) { //if any others are selected
                                                    can_clear_parent = false;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        else {
                            can_clear_parent = false;
                        }
                        return can_clear_parent;
                    },
                    'conditionalselect': function (node, event_type) {
                        var node_array = [];
                        if (node) {
                            var node_json = this.get_json(node);
                            if (!node_json.state.loaded) {
                                //folder is not loaded
                                $(element).jstree('open_node', node);
                                return false;
                            }

                            if (node.children.length > 0) {
                                //if it has children, iterate and select any leaves.
                                var node_select_array = [];
                                var node_de_select_array = [];
                                
                                for (var i = 0, len = node.children.length; i < len; i++) {
                                    if (event_type == 'select_node') {
                                        if ($(element).jstree('is_leaf', node.children[i])) {
                                            node_select_array.push(node.children[i]);
                                        }
                                    }
                                    else if (event_type == 'deselect_node') {
                                        if ($(element).jstree('is_leaf', node.children[i])) {
                                            node_de_select_array.push(node.children[i]);
                                        }
                                    }
                                }
                                if (event_type == 'select_node') {
                                    $.jstree.reference(element).select_node(node_select_array, true, true);
                                }
                                else if (event_type == 'deselect_node') {
                                    $.jstree.reference(element).deselect_node(node_de_select_array, true, true);
                                }
                                
                            }
                        }
                        return true;
                    },
                    'core': {
                        'strings' : {
                            'Loading ...': gettext('Please Wait...')
                        },
                        'data': {
                            cache: false,
                            type: 'POST',
                            url: "/rest/usb_util/list/",
                            data: function (node) { return JSON.stringify({ 'id': node.id }); },
                            dataType: 'json',
                            tryCount: 0,
                            retryLimit: 50,
                            usb_error_message: '<div class="usb_error_message">' + gettext('No USB drive was detected, please connect USB drive and press Reload to try again. If issue persists contact administrator.') + '</div>',
                            spinner_markup: '<ul class="jstree-container-ul"><li class="jstree-initial-node jstree-loading jstree-leaf jstree-last"><i class="jstree-icon jstree-ocl"></i><a class="jstree-anchor" href="#"><i class="jstree-icon jstree-themeicon-hidden"></i>' + gettext('Please Wait...') + '</a></li></ul>',
                            success: function (json) {
                                if (this.tryCount > 0 && json.length > 0) {
                                    scope.reload_page();
                                }
                                if (json.length <= 0 && this.data.id == '#') {
                                    this.tryCount++;
                                    if (this.tryCount <= this.retryLimit) {
                                        $('.usb_error_message').remove();
                                        $('#usb_browser').empty().append(this.spinner_markup);
                                        $.ajax(this);
                                        return;
                                    }
                                }
                                //will hit only if no data and retryLimit exhausted
                                if (json.length <= 0 && this.data.id == '#') {
                                    $('#usb_browser').empty()
                                    $('.usb_error_message').remove();
                                    $('#usb_browser').after(this.usb_error_message);
                                }
                                scope.reload_disabled = false;

                                scope.$apply();
                            },
                            error: function (json) {
                                $('.usb_error_message').remove();
                                $('#usb_browser').empty().after(this.usb_error_message);
                                scope.reload_disabled = false;
                                scope.$apply();
                            }
                        },
                        'themes': {
                            "variant": "large"
                        }
                    },
                    'checkbox': {
                        "three_state": false
                    },
                    "plugins": ["checkbox", "conditionalselect"]
                });/*.bind('open_node.jstree', function (evt, obj) {
                    var node = document.getElementById(obj.node.id)
                    $(node).children('a').first().removeClass('hide_my_checkbox');
                });*/
            }
        };
    }).directive("categoryhierarchy", function () {
        return {
            controller: 'CategoryHierarchyCtrl',
            restrict: "AE",
            scope :{
                onselect : "=?",
                ondeselect: "=?",
                initselected: "=?",
                filtering: "=?"
            },
            link: function (scope, element, attrs) {

                function safeString(str) {
                    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                }

                var unwatch = scope.$watch('tree', function (v) {
                    if (v) {
                        unwatch();
                        //rework data to jstree expected format
                        var data_as_array = [];
                        if (scope.filtering) {
                            data_as_array.push({ id: -1, text: gettext('Uncategorised'), name: gettext('Uncategorised'), uses: 0, locked: true, children: [] });
                        }
                        
                        if (!scope.filtering && scope.tree.results.length <= 0) {
                            $(element).after('<p>' + gettext('No categories created') + '</p>')
                        }

                        for (var i = 0; i < scope.tree.results.length; i++) {
                            scope.tree.results[i].text = safeString(scope.tree.results[i].text);
                            scope.tree.results[i].name = safeString(scope.tree.results[i].name);
                            data_as_array.push(scope.tree.results[i]);
                            delete data_as_array[i]['parent']
                        }
                        
                        $(element).on('ready.jstree', function () {
                            $(element).jstree('select_node', '' + scope.initselected); //select node and suppress the changed event
                        }).on('changed.jstree', function (node, selected) {
                            if (scope.onselect && typeof scope.onselect == 'function') {
                                if (selected.action === 'select_node') {
                                    var currNode = selected.node
                                    var text = currNode.text;
                                    while (currNode.parent != '#') {
                                        currNode = $(element).jstree('get_node', currNode.parent);
                                        text = currNode.text + ' - ' + text;
                                    }
                                    scope.onselect({ id: selected.node.id, text: text });
                                }
                                else if (scope.ondeselect && typeof scope.ondeselect == 'function') {
                                    scope.ondeselect('Category');
                                }
                                scope.$apply();
                            }
                        }).jstree({
                            'core': {
                                'data': data_as_array,
                                'multiple': false,
                                "themes": {
                                    "icons": false,
                                    "variant": "large"
                                }
                            },
                            'checkbox': {
                                "three_state": false,
                                "whole_node": false,
                                "keep_selected_style": false
                            },                            
                            "plugins": ["checkbox"]
                        }).bind("select_node.jstree deselect_node.jstree", function (evt, data) {
                            //toggle off, all nodes, then re-enable selected
                            var selected = $.jstree.reference('#' + element.attr('id')).get_selected();
                            scope.selected_id = (selected.length > 0) ? selected[0] : '0';
                            scope.$apply();
                        });
                    }
                });
            }
        };
    }).directive("preloadusbtree", function () {
        return {
            restrict: "AE",
            link: function (scope, element, attrs)
                {

                //jstree conditional select node
                (function ($, undefined) {
                    "use strict";
                    $.jstree.defaults.conditionalselect = function () { return true; };
                    $.jstree.plugins.conditionalselect = function (options, parent) {
                        this.select_node = function (obj, supress_event, prevent_open, evt) {
                            var jstree_event_type = 'select_node';
                            if (this.settings.conditionalselect.call(this, this.get_node(obj), jstree_event_type)) {
                                parent.select_node.call(this, obj, supress_event, prevent_open);
                                if (this.settings.shouldselectparent.call(this, this.get_node(obj), jstree_event_type)) {
                                    parent.select_node.call(this, this.get_node(obj).parent, supress_event, prevent_open);
                                }
                            }
                            this.settings.dofileselect.call(this, evt);
                        };
                        this.deselect_node = function (obj, supress_event, prevent_open, evt) {
                            var jstree_event_type = 'deselect_node';
                            if (this.settings.conditionalselect.call(this, this.get_node(obj), jstree_event_type)) {
                                parent.deselect_node.call(this, obj, supress_event, prevent_open);
                                //clear the parent
                                if ($(element).jstree('is_leaf', this.get_node(obj))){
                                    parent.deselect_node.call(this, this.get_node(obj).parent, supress_event, prevent_open);
                                }
                            }
                            this.settings.dofileselect.call(this, evt);
                        };
                    };
                })(jQuery);

                $(element).jstree({
                    'dofileselect': function (evt) {
                        if (evt) {
                            //console.log('user interaction');
                            scope.onFileSelect();
                        }
                        else {
                            //console.log('...other');
                        }
                    },
                    'shouldselectparent': function (node, event_type) {
                        var node_array = [];
                        var select_parent = true;

                        if (node && $(element).jstree('is_leaf', node)) {
                            //check all siblings to see if we should check or uncheck the parent
                            if (node.parent) {
                                var group_parent = $.jstree.reference(element).get_json(node.parent);
                                if (group_parent.children.length > 0) {
                                    if (event_type == 'select_node' && $(element).jstree('is_leaf', node)) {
                                        var i = 0;
                                        for (i = 0; i < group_parent.children.length; i++) {
                                            if (group_parent.children[i].id != node.id) { //only check siblings not self
                                                if (!group_parent.children[i].state['selected'] && $(element).jstree('is_leaf', group_parent.children[i])) { //if any others are not selected
                                                    select_parent = false;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        else {
                            select_parent = false;
                        }
                        return select_parent;
                    },
                    'canclearparent': function (node, event_type) {
                        var node_array = [];
                        var can_clear_parent = true;
                        
                        if (node && $(element).jstree('is_leaf', node)) {
                            //check all siblings to see if we should check or uncheck the parent
                            if (node.parent) {
                                var group_parent = $.jstree.reference(element).get_json(node.parent);
                                if (group_parent.children.length > 0) {
                                    if (event_type == 'deselect_node' && $(element).jstree('is_leaf', node)) {
                                        var i = 0;
                                        for (i = 0; i < group_parent.children.length; i++) {
                                            if (group_parent.children[i].id != node.id && $(element).jstree('is_leaf', group_parent.children[i])) { //only check sibling leaves
                                                if (group_parent.children[i].state['selected']) { //if any others are selected
                                                    can_clear_parent = false;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        else {
                            can_clear_parent = false;
                        }
                        return can_clear_parent;
                    },
                    'conditionalselect': function (node, event_type) {
                        var node_array = [];
                        if (node) {
                            var selectsingle = attrs['selectsingle'] !== undefined && attrs['selectsingle'] == 'true';

                            //prevent duplicate selection
                            if (node.text && event_type == 'select_node') {
                                if (selectsingle) {
                                    if (scope.isAnythingSelected())
                                        return false;
                                }
                                if (scope.isDuplicateSelected(node.text))
                                    return false;
                            }

                            var node_json = this.get_json(node);
                            if (!node_json.state.loaded) {
                                //folder is not loaded
                                $(element).jstree('open_node', node);
                                return false;
                            }

                            if (node.children.length > 0 && !selectsingle) {
                                //if it has children, iterate and select any leaves.
                                var node_select_array = [];
                                var node_de_select_array = [];

                                for (var i = 0, len = node.children.length; i < len; i++) {
                                    if (event_type == 'select_node') {
                                        if ($(element).jstree('is_leaf', node.children[i])) {
                                            //do not reselect if already selected (to suppress 'duplicate warning' toast)
                                            if (!$(element).jstree('is_selected', node.children[i])) {
                                                node_select_array.push(node.children[i]);
                                            }
                                        }
                                    }
                                    else if (event_type == 'deselect_node') {
                                        if ($(element).jstree('is_leaf', node.children[i])) {
                                            node_de_select_array.push(node.children[i]);
                                        }
                                    }
                                }
                                if (event_type == 'select_node') {
                                    $.jstree.reference(element).select_node(node_select_array, true, true);
                                }
                                else if (event_type == 'deselect_node') {
                                    $.jstree.reference(element).deselect_node(node_de_select_array, true, true);
                                }
                            }
                        }
                        return true;
                    },
                    'core': {
                        'strings': {
                            'Loading ...': gettext('Please Wait...')
                        },
                        'data': {
                            cache: false,
                            type: 'POST',
                            url: "/rest/usb_util/list/",
                            data: function (node) { return JSON.stringify({ 'id': node.id, filetypes: '.zip' }); },
                            dataType: 'json',
                            tryCount: 0,
                            retryLimit: 50,
                            usb_error_message: '<div class="usb_error_message">' + gettext('No USB drive was detected, please connect USB drive and press Reload to try again. If issue persists contact administrator.') + '</div>',
                            spinner_markup: '<ul class="jstree-container-ul"><li class="jstree-initial-node jstree-loading jstree-leaf jstree-last"><i class="jstree-icon jstree-ocl"></i><a class="jstree-anchor" href="#"><i class="jstree-icon jstree-themeicon-hidden"></i>' + gettext('Please Wait...') + '</a></li></ul>',
                            success: function (json) {
                                if (this.tryCount > 0 && json.length > 0) {
                                    scope.reload_page();
                                }
                                var jdata = JSON.parse(this.data);
                                if (json.length <= 0 && jdata.id == '#') {
                                    this.tryCount++;
                                    if (this.tryCount <= this.retryLimit) {
                                        $('.usb_error_message').remove();
                                        $('#usb_browser,#tile_usb_browser').empty().append(this.spinner_markup);
                                        $.ajax(this);
                                        return;
                                    }
                                }
                                //will hit only if no data and retryLimit exhausted
                                if (json.length <= 0 && jdata.id == '#') {
                                    $('#usb_browser,#tile_usb_browser').empty()
                                    $('.usb_error_message').remove();
                                    $('#usb_browser,#tile_usb_browser').after(this.usb_error_message);
                                    scope.$emit('usb-not-found');
                                }
                                scope.reload_disabled = false;

                                scope.$apply();
                            },
                            error: function (json) {
                                $('.usb_error_message').remove();
                                $('#usb_browser,#tile_usb_browser').empty().after(this.usb_error_message);
                                scope.$emit('usb-not-found');
                                scope.reload_disabled = false;
                                scope.$apply();
                            }
                        },
                        'themes': {
                            "variant": "large"
                        }
                    },
                    'checkbox': {
                        "three_state": false
                    },
                    "plugins": ["checkbox", "conditionalselect"]
                });/*.bind('open_node.jstree', function (evt, obj) {
                    var node = document.getElementById(obj.node.id)
                    $(node).children('a').first().removeClass('hide_my_checkbox');
                });*/
            }
        };
    });


}());