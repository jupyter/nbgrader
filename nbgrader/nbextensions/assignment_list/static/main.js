define(function(require) {
    var $ = require('jquery');
    var IPython = require('base/js/namespace');
    var AssignmentList = require('./assignment_list');

    var assignment_html = $([
        '<div id="assignments" class="tab-pane">',
        '  <div id="assignments_toolbar" class="row list_toolbar">',
        '    <div class="col-sm-8 no-padding">',
        '      <span id="assignments_list_info" class="toolbar_info">Released, downloaded, and submitted assignments.</span>',
        '    </div>',
        '    <div class="col-sm-4 no-padding tree-buttons">',
        '      <span id="assignments_buttons" class="pull-right toolbar_buttons">',
        '      <button id="refresh_assignments_list" title="Refresh assignments list" class="btn btn-default btn-xs"><i class="fa fa-refresh"></i></button>',
        '      </span>',
        '    </div>',
        '  </div>',
        '  <div class="panel-group">',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Released assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="released_assignments_list" class="list_container">',
        '          <div id="released_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no assignments to fetch. </div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Downloaded assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="fetched_assignments_list" class="list_container" role="tablist" aria-multiselectable="true">',
        '          <div id="fetched_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no downloaded assignments. </div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Submitted assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="submitted_assignments_list" class="list_container">',
        '          <div id="submitted_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no submitted assignments. </div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '  </div>   ',
        '</div>'
    ].join('\n'));

   function load() {
        if (!IPython.notebook_list) return;
        var base_url = IPython.notebook_list.base_url;
        $('head').append(
            $('<link>')
            .attr('rel', 'stylesheet')
            .attr('type', 'text/css')
            .attr('href', base_url + 'nbextensions/assignment_list/assignment_list.css')
        );
        $(".tab-content").append(assignment_html);
        $("#tabs").append(
            $('<li>')
            .append(
                $('<a>')
                .attr('href', '#assignments')
                .attr('data-toggle', 'tab')
                .text('Assignments')
                .click(function (e) {
                    window.history.pushState(null, null, '#assignments');
                })
            )
        );
        var assignment_list = new AssignmentList.AssignmentList(
            '#released_assignments_list',
            '#fetched_assignments_list',
            '#submitted_assignments_list',
            {
                base_url: IPython.notebook_list.base_url,
                notebook_path: IPython.notebook_list.notebook_path,
            }
        );
        assignment_list.load_list();
    }
    return {
        load_ipython_extension: load
    };
});
