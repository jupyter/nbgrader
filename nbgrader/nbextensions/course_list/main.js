define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    './course_list'
], function(Jupyter, $, utils, CourseList) {
    "use strict";

    var nbgrader_version = "0.6.1";

    var ajax = utils.ajax || $.ajax;
    // Notebook v4.3.1 enabled xsrf so use notebooks ajax that includes the
    // xsrf token in the header data

    var course_html = $([
        '<div id="courses" class="tab-pane">',
        '  <div class="alert alert-danger version_error">',
        '  </div>',
        '  <div class="panel-group">',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Available formgraders',
        '        <span id="formgrader_buttons" class="pull-right toolbar_buttons">',
        '        <button id="refresh_formgrader_list" title="Refresh formgrader list" class="btn btn-default btn-xs"><i class="fa fa-refresh"></i></button>',
        '        </span>',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="formgrader_list" class="list_container">',
        '          <div id="formgrader_list_placeholder" class="row list_placeholder">',
        '            <div> There are no available formgrader services. </div>',
        '          </div>',
        '          <div id="formgrader_list_loading" class="row list_loading">',
        '            <div> Loading, please wait... </div>',
        '          </div>',
        '          <div id="formgrader_list_error" class="row list_error">',
        '            <div></div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '  </div>   ',
        '</div>'
    ].join('\n'));

    function checkNbGraderVersion(base_url) {
        var settings = {
            cache : false,
            type : "GET",
            dataType : "json",
            data : {
                version: nbgrader_version
            },
            success : function (response) {
                if (!response['success']) {
                    var err = $("#courses .version_error");
                    err.text(response['message']);
                    err.show();
                }
            },
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(base_url, 'nbgrader_version');
        ajax(url, settings);
    }

    function load() {
        if (!Jupyter.notebook_list) return;
        var base_url = Jupyter.notebook_list.base_url;
        $('head').append(
            $('<link>')
            .attr('rel', 'stylesheet')
            .attr('type', 'text/css')
            .attr('href', base_url + 'nbextensions/course_list/course_list.css')
        );
        $(".tab-content").append(course_html);
        $("#tabs").append(
            $('<li>')
            .append(
                $('<a>')
                .attr('href', '#courses')
                .attr('data-toggle', 'tab')
                .text('Courses')
                .click(function (e) {
                    window.history.pushState(null, null, '#courses');
                    course_list.load_list();
                })
            )
        );
        var course_list = new CourseList.CourseList(
            '#formgrader_list',
            '#refresh_formgrader_list',
            {
                base_url: Jupyter.notebook_list.base_url
            }
        );
        checkNbGraderVersion(base_url);
    }
    return {
        load_ipython_extension: load
    };
});
