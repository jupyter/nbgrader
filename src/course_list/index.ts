import {
    ILayoutRestorer,
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette, MainAreaWidget, WidgetTracker } from '@jupyterlab/apputils';

import { Widget } from '@lumino/widgets';

import { requestAPI, CourseList } from './courselist';


const PLUGIN_ID = "nbgrader/course-list";
const COMMAND_NAME = "nbgrader:open-course-list";

class CourseListWidget extends Widget {
    version_alert: HTMLDivElement;
    courselist: CourseList;
    app: JupyterFrontEnd;

    constructor(app: JupyterFrontEnd) {
        super();
        this.app = app;
        var maindiv = document.createElement('div') as HTMLDivElement;
        maindiv.id = 'courses';
        maindiv.classList.add("tab-pane");

        this.version_alert = document.createElement('div') as HTMLDivElement;
        this.version_alert.classList.add('alert', 'alert-danger', 'version_error')
        this.version_alert.hidden = true;
        maindiv.appendChild(this.version_alert);

        var panelgroup = document.createElement('div') as HTMLDivElement;
        panelgroup.classList.add('panel-group');
        var panel = document.createElement('div') as HTMLDivElement;
        panel.classList.add('panel', 'panel-default');

        var panelheading = document.createElement('div') as HTMLDivElement;
        panelheading.classList.add('panel-heading');
        panelheading.textContent = 'Available formgraders';

        var formgraderbuttons = document.createElement('span') as HTMLSpanElement;
        formgraderbuttons.id = 'formgrader_buttons';
        formgraderbuttons.classList.add('pull-right', 'toolbar_buttons');

        var refreshbutton = document.createElement('button') as HTMLButtonElement;
        refreshbutton.id = 'refresh_formgrader_list';
        refreshbutton.title = 'Refresh formgrader list';
        refreshbutton.classList.add('btn', 'btn-default', 'btn-xs');

        // I have no idea why this is an italics tag, but I'm just recreating it so :/
        var buttonimg = document.createElement('i') as HTMLElement;
        buttonimg.classList.add('fa', 'fa-refresh');

        refreshbutton.appendChild(buttonimg);
        formgraderbuttons.appendChild(refreshbutton);
        panelheading.appendChild(formgraderbuttons);
        panel.appendChild(panelheading);

        var panelbody = document.createElement('div') as HTMLDivElement;
        panelbody.classList.add('panel-body');
        var formgraderlist = document.createElement('div') as HTMLDivElement;
        formgraderlist.id = 'formgrader_list';
        formgraderlist.classList.add('list_container');

        // further initialization of formgraderlist is in here
        this.courselist = new CourseList(formgraderlist, this.app);

        panelbody.appendChild(formgraderlist);
        panel.appendChild(panelbody);
        panelgroup.appendChild(panel);
        maindiv.appendChild(panelgroup);
        this.node.appendChild(maindiv);
        this.node.style.overflowY = 'auto';

        refreshbutton.onclick = () => this.courselist.load_list.call(this.courselist);
        this.checkNbGraderVersion();
        this.courselist.load_list();
    }

    checkNbGraderVersion() {
        let nbgrader_version = '0.8.4';
        requestAPI<any>('nbgrader_version?version='+nbgrader_version)
            .then(response => {
                if (!response['success']) {
                    this.version_alert.textContent = response['message'];
                    this.version_alert.hidden = false;
                }
            })
            .catch(reason => {
                console.error(
                    `The course_list server extension appears to be missing.\n${reason}`
                );
            });
    }
}

/**
 * Initialization data for the course_list extension.
 */
export const course_list_extension: JupyterFrontEndPlugin<void> = {
    id: PLUGIN_ID,
    autoStart: true,
    requires: [ICommandPalette],
    optional: [ILayoutRestorer],

    activate: async (
      app: JupyterFrontEnd,
      palette: ICommandPalette,
      restorer: ILayoutRestorer | null
    ) => {

        let widget: MainAreaWidget<CourseListWidget>;

        const command:string = COMMAND_NAME;

        // Track the widget state
        let tracker = new WidgetTracker<MainAreaWidget<CourseListWidget>>({
            namespace: 'nbgrader-course-list'
        });

        app.commands.addCommand(command, {
            label: 'Course List',
            execute: () => {
                if (!widget || widget.isDisposed) {
                    const content = new CourseListWidget(app);
                    widget = new MainAreaWidget({content});
                    widget.id = 'nbgrader-course-list'
                    widget.addClass('nbgrader-mainarea-widget');
                    widget.title.label = 'Courses'
                    widget.title.closable = true;
                }
                if (!tracker.has(widget)) {
                    tracker.add(widget);
                }
                if (!widget.isAttached) {
                    app.shell.add(widget, 'main');
                }
                widget.content.update();
                app.shell.activateById(widget.id);
            }
        })

        palette.addItem({ command, category: "nbgrader" });

        // Restore the widget state
        if (restorer != null){
            restorer.restore(tracker, {
                command,
                name: () => 'nbgrader-course-list'
            });
        }

        console.log('JupyterLab extension course-list is activated!');
  }
};

export default course_list_extension;
