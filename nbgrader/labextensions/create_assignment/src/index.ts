import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the create_assignment extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'create-assignment',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension create-assignment is activated!');
  }
};

export default extension;
