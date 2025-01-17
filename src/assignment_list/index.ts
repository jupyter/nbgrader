import { JupyterFrontEnd } from '@jupyterlab/application';

import { Widget } from '@lumino/widgets';

import {
  PageConfig
} from '@jupyterlab/coreutils';

import {
  requestAPI,
  CourseList,
  AssignmentList
} from './assignmentlist';

export class AssignmentListWidget extends Widget {

  app: JupyterFrontEnd;

  constructor(app: JupyterFrontEnd) {
    super();
    this.app = app;

    var assignment_html = ([
      '<div id="assignments" class="tab-pane">',
      '  <div id="assignments_toolbar" class="row list_toolbar">',
      '    <div class="col-sm-8 no-padding">',
      '      <span id="assignments_list_info" class="toolbar_info">Released, downloaded, and submitted assignments for course:</span>',
      '      <div class="btn-group btn-group-xs">',
      '        <button type="button" class="btn btn-default" id="course_list_default">Loading, please wait...</button>',
      '        <button type="button" class="btn btn-default dropdown-toggle" id="course_list_dropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" disabled="disabled">',
      '          <span class="caret"></span>',
      '          <span class="sr-only">Toggle Dropdown</span>',
      '        </button>',
      '        <ul class="dropdown-menu" id="course_list">',
      '        </ul>',
      '      </div>',
      '    </div>',
      '    <div class="col-sm-4 no-padding tree-buttons">',
      '      <span id="assignments_buttons" class="pull-right toolbar_buttons">',
      '      <button id="refresh_assignments_list" title="Refresh assignments list" class="btn btn-default btn-xs"><i class="fa fa-refresh"></i></button>',
      '      </span>',
      '    </div>',
      '  </div>',
      '  <div class="alert alert-danger version_error">',
      '  </div>',
      '  <div class="panel-group">',
      '    <div class="panel panel-default">',
      '      <div class="panel-heading">',
      '        Released assignments',
      '      </div>',
      '      <div class="panel-body">',
      '        <div id="released_assignments_list" class="list_container">',
      '          <div id="released_assignments_list_placeholder" class="list_placeholder">',
      '            <div> There are no assignments to fetch. </div>',
      '          </div>',
      '          <div id="released_assignments_list_loading" class="list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="released_assignments_list_error" class="list_error">',
      '            <div></div>',
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
      '          <div id="fetched_assignments_list_placeholder" class="list_placeholder">',
      '            <div> There are no downloaded assignments. </div>',
      '          </div>',
      '          <div id="fetched_assignments_list_loading" class="list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="fetched_assignments_list_error" class="list_error">',
      '            <div></div>',
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
      '          <div id="submitted_assignments_list_placeholder" class="list_placeholder">',
      '            <div> There are no submitted assignments. </div>',
      '          </div>',
      '          <div id="submitted_assignments_list_loading" class="list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="submitted_assignments_list_error" class="list_error">',
      '            <div></div>',
      '          </div>',
      '        </div>',
      '      </div>',
      '    </div>',
      '  </div>   ',
      '</div>'
  ].join('\n'));

    this.node.innerHTML = assignment_html;
    this.node.style.overflowY = 'auto';

    let base_url = PageConfig.getBaseUrl();
    let options = new Map();
    options.set('base_url',base_url);
    var assignment_l = new AssignmentList(this,
      'released_assignments_list',
      'fetched_assignments_list',
      'submitted_assignments_list',
      options,
      this.app);

    new CourseList(this,
      'course_list',
      'course_list_default',
      'course_list_dropdown',
      'refresh_assignments_list',
      assignment_l,
      options
    );

    this.checkNbGraderVersion();

  }

  checkNbGraderVersion() {
    var warning = this.node.getElementsByClassName('version_error')[0] as HTMLDivElement;
    warning.hidden=false;
    requestAPI<any>('nbgrader_version?version='+"0.9.5")
    .then(response => {
        if (!response['success']) {
          warning.innerText = response['message'];
          warning.style.display = 'block'
        }
    })
    .catch(reason => {
        console.error(
          `Error on GET /assignment_list/nbgrader_version.\n${reason}`
        );
    });
  }

}
