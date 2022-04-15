import {
  ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin
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

  app: JupyterFrontEnd;

  constructor(app: JupyterFrontEnd) {
    super();
    this.app = app;
    var h = document.getElementsByTagName('head')[0] as HTMLHeadElement;
    console.log('Initializing the assignments list widget');
    var l = document.createElement('link') as HTMLLinkElement;
    l.rel = 'stylesheet';
    l.href = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css'
    l.type = 'text/css'

    var s1 = document.createElement('script') as HTMLScriptElement;
    s1.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js'
    s1.type = 'text/javascript'
    s1.crossOrigin = 'anonymous'
    s1.async = false;
    var s2 = document.createElement('script') as HTMLScriptElement;
    s2.src = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js'
    s2.type = 'text/javascript'
    s2.async=false;

    h.append(l)
    h.append(s1)
    h.append(s2)

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
      '</div>'
  ].join('\n'));
    var html = document.createElement('div') as HTMLDivElement;
    html.innerHTML=assignment_html;
    this.node.append(html);

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
    requestAPI<any>('nbgrader_version?version='+"0.7.0.dev")
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
          const content = new AssignmentListWidget(app);
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
    palette.addItem({command, category: 'nbgrader'});

    // Track and restore the widget state
    let tracker = new WidgetTracker<MainAreaWidget<AssignmentListWidget>>({
    namespace: 'al'
    });
    restorer.restore(tracker, {
      command,
      name: () => 'al'
    });


  }
};

export default assignment_list_extension;
