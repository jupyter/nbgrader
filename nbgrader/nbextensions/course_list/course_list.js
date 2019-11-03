// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(Jupyter, $, utils, dialog) {
    "use strict";

    var ajax = utils.ajax || $.ajax;
    // Notebook v4.3.1 enabled xsrf so use notebooks ajax that includes the
    // xsrf token in the header data

    var CourseList = function (course_list_selector, refresh_selector, options) {
        this.course_list_selector = course_list_selector;
        this.refresh_selector = refresh_selector;

        this.course_list_element = $(course_list_selector);
        this.refresh_element = $(refresh_selector);

        this.current_course = undefined;
        this.bind_events()

        options = options || {};
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");

        this.data = undefined;
    };

    CourseList.prototype.bind_events = function () {
        var that = this;
        this.refresh_element.click(function () {
            that.load_list();
        });
    };


    CourseList.prototype.clear_list = function (loading) {
        this.course_list_element.children('.list_item').remove();
        if (loading) {
            // show loading
            this.course_list_element.children('.list_loading').show();
            // hide placeholders and errors
            this.course_list_element.children('.list_placeholder').hide();
            this.course_list_element.children('.list_error').hide();

        } else {
            // show placeholders
            this.course_list_element.children('.list_placeholder').show();
            // hide loading and errors
            this.course_list_element.children('.list_loading').hide();
            this.course_list_element.children('.list_error').hide();
        }
    };

    CourseList.prototype.show_error = function (error) {
        this.course_list_element.children('.list_item').remove();
        // show errors
        this.course_list_element.children('.list_error').show();
        this.course_list_element.children('.list_error').text(error);
        // hide loading and placeholding
        this.course_list_element.children('.list_loading').hide();
        this.course_list_element.children('.list_placeholder').hide();
    };

    CourseList.prototype.load_list = function () {
        this.clear_list(true);

        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.handle_load_list, this),
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(this.base_url, 'formgraders');
        ajax(url, settings);
    };

    CourseList.prototype.handle_load_list = function (data, status, xhr) {
        if (data.success) {
            this.load_list_success(data.value);
        } else {
            this.show_error(data.value);
        }
    };

    CourseList.prototype.load_list_success = function (data) {
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var element = $('<div/>');
            var item = new Course(element, data[i], this.course_list_selector, $.proxy(this.handle_load_list, this), this.options);
            this.course_list_element.append(element);
            this.course_list_element.children('.list_placeholder').hide()
        }

        if (this.callback) {
            this.callback();
            this.callback = undefined;
        }
    };

    var Course = function (element, data, parent, on_refresh, options) {
        this.element = $(element);
        this.course_id = data['course_id'];
        this.formgrader_kind = data['kind'];
        this.url = data['url'];
        this.parent = parent;
        this.on_refresh = on_refresh;
        this.options = options;
        this.style();
        this.make_row();
    };

    Course.prototype.style = function () {
        this.element.addClass('list_item').addClass("row");
    };

    Course.prototype.make_row = function () {
        var row = $('<div/>').addClass('col-md-12');
        var course_id = this.course_id;

        if(course_id === '') {
            course_id = 'Default formgrader';
        }

        var container = $('<span/>').addClass('item_name col-sm-2').append(
            $('<a/>')
                .attr('href', this.url)
                .attr('target', '_blank')
                .text(course_id));
        row.append(container);
        row.append($('<span/>').addClass('item_course col-sm-2').text(this.formgrader_kind));
        this.element.empty().append(row);
    };

    return {
        'CourseList': CourseList
    };
});
