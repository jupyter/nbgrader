import { ILabShell, ILayoutRestorer, IRouter, JupyterFrontEnd, JupyterFrontEndPlugin } from "@jupyterlab/application";
import { ICommandPalette, MainAreaWidget, WidgetTracker } from "@jupyterlab/apputils";
import { PageConfig, URLExt } from "@jupyterlab/coreutils";
import { IMainMenu } from '@jupyterlab/mainmenu';
import { INotebookTracker } from "@jupyterlab/notebook";
import { ServerConnection } from "@jupyterlab/services";
import { INotebookShell } from "@jupyter-notebook/application";
import { INotebookTree } from "@jupyter-notebook/tree";
import { Menu, Panel } from '@lumino/widgets';

import { AssignmentListWidget } from "./assignment_list/index";
import { FormgraderWidget } from "./formgrader/index";
import { CourseListWidget } from "./course_list/index";
import { CreateAssignmentWidget } from "./create_assignment/index";
import { ButtonExtension } from "./validate_assignment/index";

/**
 * The plugin IDs
 */
const pluginIDs = {
  menus: '@jupyter/nbgrader:menu',
  assignmentsList: '@jupyter/nbgrader:assignment-list',
  coursesList: '@jupyter/nbgrader:course-list',
  formgrader: '@jupyter/nbgrader:formgrader',
  createAssignment: '@jupyter/nbgrader:create-assignment',
  validateAssignment: '@jupyter/nbgrader:validate-assignment'
}

/**
 * The command IDs
 */
export const commandIDs = {
  openAssignmentsList: 'nbgrader:open-assignment-list',
  openCoursesList: 'nbgrader:open-course-list',
  openFormgrader: 'nbgrader:open-formgrader',
  openCreateAssignment: 'nbgrader:open-create-assignment'
}

/**
 * Manage the extensions available in Notebook.
 */
const availableExtensionsManager: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.menus,
  autoStart: true,
  requires: [IMainMenu],
  optional: [ICommandPalette, ILabShell, INotebookShell],
  activate: (
    app: JupyterFrontEnd,
    mainMenu: IMainMenu,
    palette: ICommandPalette,
    labShell: ILabShell,
    notebookShell: INotebookShell
  ) => {

    let mainExtensions = false;
    let createExtension = false;
    if (notebookShell) {
      const page = PageConfig.getOption('notebookPage');
      if (page === 'tree') {
        mainExtensions = true;
      } else if (page === 'notebooks') {
        createExtension = true;
      }
    }

    if (!(labShell || mainExtensions || createExtension)) {
      return
    }

    const nbgraderMenu = new Menu({ commands: app.commands });
    nbgraderMenu.id = 'jp-mainmenu-nbgrader';
    nbgraderMenu.title.label = 'Nbgrader';

    if (mainExtensions || labShell) {
      nbgraderMenu.addItem({ command: commandIDs.openAssignmentsList });
      nbgraderMenu.addItem({ command: commandIDs.openCoursesList });
      nbgraderMenu.addItem({ command: commandIDs.openFormgrader });

      if (palette) {
        palette.addItem({
          command: commandIDs.openAssignmentsList,
          category: 'nbgrader'
        });
        palette.addItem({
          command: commandIDs.openCoursesList,
          category: 'nbgrader'
        });
        palette.addItem({
          command: commandIDs.openFormgrader,
          category: 'nbgrader'
        });
      }
    }

    if (createExtension || labShell) {
      nbgraderMenu.addItem({ command: commandIDs.openCreateAssignment });

      if (palette) {
        palette.addItem({
          command: commandIDs.openCreateAssignment,
          category: 'nbgrader'
        });
      }
    }

    mainMenu.addMenu(nbgraderMenu);
  }
}

/**
 * Assignment list plugin.
 */
const assignmentListExtension: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.assignmentsList,
  autoStart: true,
  optional: [ILayoutRestorer, INotebookTree],
  activate: (
    app: JupyterFrontEnd,
    restorer: ILayoutRestorer | null,
    notebookTree: INotebookTree | null
  ) => {

    // Declare a widget variable
    let widget: MainAreaWidget<AssignmentListWidget>;

    // Track the widget state
    let tracker = new WidgetTracker<MainAreaWidget<AssignmentListWidget>>({
      namespace: 'nbgrader-assignment-list'
    });

    app.commands.addCommand(commandIDs.openAssignmentsList, {
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

    // Restore the widget state
    if (restorer != null) {
      restorer.restore(tracker, {
        command: commandIDs.openAssignmentsList,
        name: () => 'nbgrader-assignment-list'
      });
    }

    console.debug('JupyterLab extension assignment-list is activated!');
  }
};

/**
 * Courses list plugin.
 */
const courseListExtension: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.coursesList,
  autoStart: true,
  optional: [ILayoutRestorer, INotebookTree],
  activate: (
    app: JupyterFrontEnd,
    restorer: ILayoutRestorer | null,
    notebookTree: INotebookTree | null
  ) => {

    let widget: MainAreaWidget<CourseListWidget>;

    // Track the widget state
    let tracker = new WidgetTracker<MainAreaWidget<CourseListWidget>>({
      namespace: 'nbgrader-course-list'
    });

    app.commands.addCommand(commandIDs.openCoursesList, {
      label: 'Course List',
      execute: () => {
        if (!widget || widget.isDisposed) {
          const content = new CourseListWidget(app, notebookTree !== null);
          widget = new MainAreaWidget({content});
          widget.id = 'nbgrader-course-list';
          widget.addClass('nbgrader-mainarea-widget');
          widget.title.label = 'Courses';
          widget.title.closable = true;
        }
        if (!tracker.has(widget)) {
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
    })

    // Restore the widget state
    if (restorer != null){
      restorer.restore(tracker, {
        command: commandIDs.openCoursesList,
        name: () => 'nbgrader-course-list'
      });
    }

    console.debug('JupyterLab extension course-list is activated!');
  }
};

/**
 * Formgrader extension.
 */
const formgraderExtension: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.formgrader,
  autoStart: true,
  optional: [ILayoutRestorer, INotebookTree, IRouter],
  activate: (
    app: JupyterFrontEnd,
    restorer: ILayoutRestorer | null,
    notebookTree: INotebookTree | null,
    router: IRouter | null
  ) => {
    // Declare a widget variable
    let widget: MainAreaWidget<FormgraderWidget>;

    // Track the widget state
    let tracker = new WidgetTracker<MainAreaWidget<FormgraderWidget>>({
      namespace: 'nbgrader-formgrader'
    });

    app.commands.addCommand(commandIDs.openFormgrader, {
    label: 'Formgrader',
    execute: args => {
      if (!widget || widget.isDisposed) {
        const settings = ServerConnection.makeSettings();
        const url = (args.url as string) || URLExt.join(settings.baseUrl, "formgrader");

        const content = new FormgraderWidget(app, url);

        widget = new MainAreaWidget({content});
        widget.id = 'formgrader';
        widget.title.label = 'Formgrader';
        widget.title.closable = true;
        }

        if (!tracker.has(widget)) {
          // Track the state of the widget for later restoration
          tracker.add(widget);
        }

        // Attach the widget to the main area if it's not there
        if (notebookTree){
          if (!widget.isAttached){
            notebookTree.addWidget(widget);
          }
          notebookTree.currentWidget = widget;
        } else if (!widget.isAttached) {
          app.shell.add(widget, 'main');
        }

        widget.content.update();

        app.shell.activateById(widget.id);
      }
    });

    // Open formgrader from URL.
    if (router) {
      const formgraderPattern = /(\?|&)formgrader=true/;
      router.register({
        command: commandIDs.openFormgrader,
        pattern: formgraderPattern
      });
    }

    // Restore the widget state
    if (restorer != null){
      restorer.restore(tracker, {
        command: commandIDs.openFormgrader,
        name: () => 'nbgrader-formgrader'
      });
    }
    console.debug('JupyterLab extension formgrader is activated!');
  }
};

/**
 * Create assignment plugin.
 */
const createAssignmentExtension: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.createAssignment,
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ILabShell],
  activate: (
    app: JupyterFrontEnd,
    tracker: INotebookTracker,
    labShell: ILabShell | null
  ) => {
    const panel = new Panel();
    panel.node.style.overflowY = 'auto';
    const createAssignmentWidget = new CreateAssignmentWidget(tracker, labShell);
    panel.addWidget(createAssignmentWidget);
    panel.id = 'nbgrader-create_assignemnt';
    panel.title.label = 'Create Assignment';
    panel.title.caption = 'Nbgrader Create Assignment';

    app.shell.add(panel, 'right');

    app.commands.addCommand(commandIDs.openCreateAssignment, {
      label: 'Create assignment',
      isEnabled: () => {
        return createAssignmentWidget.isAvailable();
      },
      execute: () => {
        app.shell.activateById(panel.id);
      }
    })
    console.debug('Extension "create_assignment" activated.');
  }
};


/**
 * Validate assignment plugin.
 */
const validateAssignmentExtension: JupyterFrontEndPlugin<void> = {
  id: pluginIDs.validateAssignment,
  autoStart: true,
  requires: [INotebookTracker],
  activate: (app: JupyterFrontEnd) => {
    app.docRegistry.addWidgetExtension('Notebook', new ButtonExtension());
    console.debug('JupyterLab extension validate-assignment is activated!');
  }
};

export default [
  availableExtensionsManager,
  formgraderExtension,
  assignmentListExtension,
  courseListExtension,
  createAssignmentExtension,
  validateAssignmentExtension
]
