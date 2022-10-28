import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette,
  MainAreaWidget,
  WidgetTracker
} from '@jupyterlab/apputils';

import {
  Widget,
  // TabPanel
} from '@lumino/widgets';

import {
  PageConfig
} from '@jupyterlab/coreutils';

import { INotebookTree } from '@jupyter-notebook/tree';

import {
  requestAPI,
  CourseList,
  AssignmentList
} from './assignmentlist';


const PLUGIN_ID = 'nbgrader:assignment-list';
const COMMAND_NAME = "nbgrader:open-assignment-list";


class AssignmentListWidget extends Widget {

  app: JupyterFrontEnd;

  constructor(app: JupyterFrontEnd) {
    super();
    this.app = app;

    console.log('Initializing the assignments list widget');

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
    requestAPI<any>('nbgrader_version?version='+"0.8.4")
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

export const assignment_list_extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICommandPalette],
  optional: [ILayoutRestorer, INotebookTree],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    restorer: ILayoutRestorer | null,
    notebookTree: INotebookTree | null
  )=> {

    // Declare a widget variable
    let widget: MainAreaWidget<AssignmentListWidget>;

    // Add an application command
    const command: string = COMMAND_NAME;

    // Track the widget state
    let tracker = new WidgetTracker<MainAreaWidget<AssignmentListWidget>>({
      namespace: 'nbgrader-assignment-list'
    });

    app.commands.addCommand(command,{
      label: 'Assignment List',
      execute: () => {
        if(!widget || widget.isDisposed){
          const content = new AssignmentListWidget(app);
          widget = new MainAreaWidget({content});
          widget.id = 'nbgrader-assignment-list';
          widget.addClass('nbgrader-mainarea-widget');
          widget.title.label = 'Assignments';
          widget.title.closable = true;
        }
        if(!tracker.has(widget)){
          // Track the state of the widget for later restoration
          tracker.add(widget);
        }

        // Attach the widget to the main area if it's not there
        if(!widget.isAttached){
          if (notebookTree){
            notebookTree.addWidget(widget);
            notebookTree.currentWidget = widget;
          }
          else app.shell.add(widget, 'main');
        }

        widget.content.update();

        app.shell.activateById(widget.id);
      }
    });

    // Add the command to the palette
    palette.addItem({command, category: 'nbgrader'});

    // Restore the widget state
    if (restorer != null) {
      restorer.restore(tracker, {
        command,
        name: () => 'nbgrader-assignment-list'
      });
    }

    console.debug('JupyterLab extension assignment-list is activated!');
  }
};

export default assignment_list_extension;
