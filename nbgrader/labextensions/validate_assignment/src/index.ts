import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './validateassignment';

/**
 * Initialization data for the validate_assignment extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'validate-assignment',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension validate-assignment is activated!');

    requestAPI<any>('get_example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The validate_assignment server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default extension;
