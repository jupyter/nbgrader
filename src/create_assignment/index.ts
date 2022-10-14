import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILabShell
} from '@jupyterlab/application';

import {
  INotebookTracker
} from '@jupyterlab/notebook';

import {
  Panel
} from '@lumino/widgets';


import {
  CreateAssignmentWidget
} from './create_assignment_extension';

const PLUGIN_ID = "nbgrader:create-assignment"

/**
 * Initialization data for the create_assignment extension.
 */
export const create_assignment_extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ILabShell],
  activate: activate_extension
};

/**
 *
 * @param app JupyterFrontEnd
 * @param tracker track any changes on the Notebook
 * @param labShell used only to track if the main area of JupyterLab has a Notebook in frontend.
 */
function activate_extension (
  app: JupyterFrontEnd,
  tracker: INotebookTracker,
  labShell: ILabShell | null
) {
  const panel = new Panel();
  panel.node.style.overflowY = 'auto';
  const createAssignmentWidget = new CreateAssignmentWidget(tracker, labShell);
  panel.addWidget(createAssignmentWidget);
  panel.id = 'nbgrader-create_assignemnt';
  panel.title.label = 'Create Assignment';
  panel.title.caption = 'nbgrader Create Assignment';

  app.shell.add(panel, 'right');
  console.debug('Extension "create_assignment" activated.');
}

export default create_assignment_extension;
