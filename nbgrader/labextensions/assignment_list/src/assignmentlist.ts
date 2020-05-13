import {
  ILayoutRestorer, JupyterFrontEnd,JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette, MainAreaWidget, WidgetTracker
} from '@jupyterlab/apputils';

import {
  Widget
} from '@lumino/widgets';

import { 
  PageConfig 
} from '@jupyterlab/coreutils';

import { requestAPI, CourseList, AssignmentList } from './assignmentlist';



class AssignmentListWidget extends Widget {
  
  constructor() {
    super();
    console.log('Initializing the assignments list widget');
    var assignment_html = ([
      '<head>',
      '  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">',
      '</head>',
      '<div id="assignments" class="tab-pane">',
      '  <div id="assignments_toolbar" class="row list_toolbar">',
      '    <div class="col-sm-8 no-padding">',
      '      <span id="assignments_list_info" class="toolbar_info">Released, downloaded, and submitted assignments for course:</span>',
      '      <div id="course_drop_down" class="btn-group btn-group-xs">',
      '        <button type="button" class="btn btn-default" id="course_list_default">Loading, please wait...</button>',
      '        <button type="button" class="btn btn-default dropdown-toggle" id="course_list_dropdown" data-toggle="dropdown" disabled="disabled">',
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
      '          <div id="released_assignments_list_placeholder" class="row list_placeholder">',
      '            <div> There are no assignments to fetch. </div>',
      '          </div>',
      '          <div id="released_assignments_list_loading" class="row list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="released_assignments_list_error" class="row list_error">',
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
      '          <div id="fetched_assignments_list_placeholder" class="row list_placeholder">',
      '            <div> There are no downloaded assignments. </div>',
      '          </div>',
      '          <div id="fetched_assignments_list_loading" class="row list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="fetched_assignments_list_error" class="row list_error">',
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
      '          <div id="submitted_assignments_list_placeholder" class="row list_placeholder">',
      '            <div> There are no submitted assignments. </div>',
      '          </div>',
      '          <div id="submitted_assignments_list_loading" class="row list_loading">',
      '            <div> Loading, please wait... </div>',
      '          </div>',
      '          <div id="submitted_assignments_list_error" class="row list_error">',
      '            <div></div>',
      '          </div>',
      '        </div>',
      '      </div>',
      '    </div>',
      '  </div>   ',
      '</div>',
    ].join('\n'));
    
    this.node.insertAdjacentHTML('beforeend', assignment_html);
    let base_url = PageConfig.getBaseUrl();
    let options = new Map();
    options.set('base_url',base_url);
    var assignment_l = new AssignmentList(this,
      'released_assignments_list',
      'fetched_assignments_list',
      'submitted_assignments_list',
      options);
 
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
    var nbgrader_version = "0.7.0.dev-SOME_CHANGE";
    var warning = this.node.getElementsByClassName('version_error')[0] as HTMLDivElement;
    warning.hidden=false;
    requestAPI<any>('nbgrader_version?version='+nbgrader_version)
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


const extension: JupyterFrontEndPlugin<void> = {
  id: 'assignment-list',
  autoStart: true,
  requires: [ICommandPalette, ILayoutRestorer],
  activate: async (app: JupyterFrontEnd, palette: ICommandPalette, restorer: ILayoutRestorer)=> {
    console.log('JupyterLab extension assignment-list is activated!');

    // Declare a widget variable
    let widget: MainAreaWidget<AssignmentListWidget>;

    // Add an application command
    const command: string = 'al:open';

    app.commands.addCommand(command,{
      label: 'Assignment List',
      execute: () => {
        if(!widget){
          const content = new AssignmentListWidget();
          widget = new MainAreaWidget({content});
          widget.id = 'assignments';
          widget.title.label = 'Assignments';
          widget.title.closable = true;
        }

        if(!tracker.has(widget)){
          // Track the state of the widget for later restoration
          tracker.add(widget);
        }
        if(!widget.isAttached){
          // Attach the widget to the mainwork area if it's not there
          app.shell.add(widget, 'main');
        }
        widget.content.update();

        // Activate the widget
        app.shell.activateById(widget.id);
      }
    });

    // Add the command to the palette
    palette.addItem({command, category: 'Assignment List'});

    // Track and restore the widget state
    let tracker = new WidgetTracker<MainAreaWidget<AssignmentListWidget>>({
    namespace: 'al'
    });
    restorer.restore(tracker, {
      command,
      name: () => 'al'
    });

    // GET request
    try {
      const data = await requestAPI<any>('get_example');
      console.log(data);
    } catch (reason) {
      console.error(`Error on GET /assignment_list/hello.\n${reason}`);
    }


    
  }
};

export default extension;
