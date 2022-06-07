import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  INotebookTracker
} from '@jupyterlab/notebook';

import {
  Panel, PanelLayout
} from '@lumino/widgets';

import {
  CreateAssignmentWidget
} from './create_assignment_extension';

/**
 * Initialization data for the create_assignment extension.
 */
export const create_assignment_extension: JupyterFrontEndPlugin<void> = {
  id: 'create-assignment',
  autoStart: true,
  requires: [INotebookTracker],
  activate: activate_extension
};

function activate_extension(app: JupyterFrontEnd, tracker: INotebookTracker) {
  console.log('Activating extension "create_assignment".');
  const panel = new Panel({layout: new PanelLayout({fitPolicy: 'set-min-size'})});
  const createAssignmentWidget = new CreateAssignmentWidget(tracker);
  panel.addWidget(createAssignmentWidget);
  panel.id = 'nbgrader-create_assignemnt';
  panel.title.label = 'Create Assignment';
  panel.title.caption = 'nbgrader Create Assignment';
  app.shell.add(panel, 'right');
  console.log('Extension "create_assignment" activated.');
}

export default create_assignment_extension;
