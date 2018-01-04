/// <reference path="../../angularjs/angular.js" />
(function () {
    "use strict"

    angular.module("taDirectives", []).directive('match', function () {
        return {
            require: 'ngModel',
            restrict: 'A',
            scope: {
                match: '='
            },
            link: function (scope, elem, attrs, ctrl) {
                scope.$watch(function () {
                    return (ctrl.$pristine && angular.isUndefined(ctrl.$modelValue)) || scope.match === ctrl.$modelValue;
                }, function (currentValue) {
                    ctrl.$setValidity('match', currentValue);
                });
            }
        };
         /**
        * Checklist-model
        * AngularJS directive for list of checkboxes
        */
       }).directive('checklistModel', ['$parse', '$compile', function ($parse, $compile) {
    // contains
        function contains(arr, item) {
            if (angular.isArray(arr)) {
                for (var i = 0; i < arr.length; i++) {
                    if (angular.equals(arr[i], item)) {
                        return true;
                    }
                }
            }
            return false;
        }

        // add
        function add(arr, item) {
            arr = angular.isArray(arr) ? arr : [];
            for (var i = 0; i < arr.length; i++) {
                if (angular.equals(arr[i], item)) {
                    return arr;
                }
            }
            arr.push(item);
            return arr;
        }

        // remove
        function remove(arr, item) {
            if (angular.isArray(arr)) {
                for (var i = 0; i < arr.length; i++) {
                    if (angular.equals(arr[i], item)) {
                        arr.splice(i, 1);
                        break;
                    }
                }
            }
            return arr;
        }

        // http://stackoverflow.com/a/19228302/1458162
        function postLinkFn(scope, elem, attrs) {
            // compile with `ng-model` pointing to `checked`
            $compile(elem)(scope);

            // getter / setter for original model
            var getter = $parse(attrs.checklistModel);
            var setter = getter.assign;

            // value added to list
            var value = $parse(attrs.checklistValue)(scope.$parent);

            // watch UI checked change
            scope.$watch('checked', function (newValue, oldValue) {
                if (newValue === oldValue) {
                    return;
                }
                var current = getter(scope.$parent);
                if (newValue === true) {
                    setter(scope.$parent, add(current, value));
                } else {
                    setter(scope.$parent, remove(current, value));
                }
            });

            // watch original model change
            scope.$parent.$watch(attrs.checklistModel, function (newArr, oldArr) {
                scope.checked = contains(newArr, value);
            }, true);
        }

        return {
            restrict: 'A',
            priority: 1000,
            terminal: true,
            scope: true,
            compile: function (tElement, tAttrs) {
                if (tElement[0].tagName !== 'INPUT' || !tElement.attr('type', 'checkbox')) {
                    throw 'checklist-model should be applied to `input[type="checkbox"]`.';
                }

                if (!tAttrs.checklistValue) {
                    throw 'You should provide `checklist-value`.';
                }

                // exclude recursion
                tElement.removeAttr('checklist-model');

                // local scope var storing individual checkbox model
                tElement.attr('ng-model', 'checked');

                return postLinkFn;
            }
        };
       }]).directive("usbtree", function (RecursionHelper) {
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
                               }
                               this.settings.dofileselect.call(this, evt);
                           };
                           this.deselect_node = function (obj, supress_event, prevent_open, evt) {
                               var jstree_event_type = 'deselect_node';
                               if (this.settings.conditionalselect.call(this, this.get_node(obj), jstree_event_type)) {
                                   parent.deselect_node.call(this, obj, supress_event, prevent_open);
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
                                   var node_array = [];

                                   for (var i = 0, len = node.children.length; i < len; i++) {
                                       if (event_type == 'select_node') {
                                           if ($(element).jstree('is_leaf', node.children[i])) {
                                               node_array.push(node.children[i]);
                                           }
                                       }
                                       else {
                                           $.jstree.reference(element).deselect_node(node.children[i], true, true);
                                       }
                                   }
                                   if (event_type == 'select_node') {
                                       $.jstree.reference(element).select_node(node_array, true, true);
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
                               data: function (node) { return JSON.stringify({ 'id': node.id , filetypes: '.zip' }); },
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
       });
}());