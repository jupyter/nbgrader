import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  INotebookTracker
} from '@jupyterlab/notebook';

import {
  BoxPanel
} from '@lumino/widgets';

import {
  CreateAssignmentWidget
} from './extension';

/**
 * Initialization data for the create_assignment extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'create-assignment',
  autoStart: true,
  requires: [INotebookTracker],
  activate: activate_extension
};

function activate_extension(app: JupyterFrontEnd, tracker: INotebookTracker) {
  console.log('Activating extension "create_assignment".');
  const panel = new BoxPanel();
  const createAssignmentWidget = new CreateAssignmentWidget(tracker);
  panel.addWidget(createAssignmentWidget);
  panel.id = 'nbgrader-create_assignemnt';
  app.shell.add(panel, 'right');
  console.log('Extension "create_assignment" activated.');
}

export default extension;
