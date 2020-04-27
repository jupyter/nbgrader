import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  IDisposable, DisposableDelegate
} from '@lumino/disposable';

import {
  ToolbarButton, Dialog, showDialog
} from '@jupyterlab/apputils';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import { requestAPI } from './validateassignment';

function error_dialog(body: string): void {
  showDialog({
    title: "Validation failed",
    body: body,
    buttons: [Dialog.okButton()],
    focusNodeSelector: 'input'
  });
}

var nbgrader_version = "0.7.0.dev"; // TODO: hardcoded value

export
class ButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let callback = () => {
      requestAPI<any>('nbgrader_version?version=' + nbgrader_version)
        .then(data => {
          if (data.success) {
            // TODO: button.title = "Saving...";
            // tests/test-docregistry/src/context.spec.ts:98
            const notebookSaved = (
              sender: DocumentRegistry.IContext<INotebookModel>,
              args: DocumentRegistry.SaveState) => {
              if (args == "completed") {
                panel.context.saveState.disconnect(notebookSaved);
                // TODO: button.title = 'Validating...'
                // TODO: btn.attr('disabled', 'disabled');
                requestAPI<any>('assignments/validate?path=TODO_UNKNOWN_PATH')
                  .then(data => {
                    error_dialog("TODO1");
                    /*
                    showDialog({
                      title: "My Dialog",
                      body: JSON.stringify(data),
                      buttons: [Dialog.okButton()],
                      focusNodeSelector: 'input'
                    });
                    */
                  })
                  .catch(reason => {
                    error_dialog(`TODO2: ${reason}`);
                  });
              } else if (args == "failed") {
                panel.context.saveState.disconnect(notebookSaved);
                error_dialog("Cannot save notebook");
              }
            };
            panel.context.saveState.connect(notebookSaved);
            // examples/notebook/src/commands.ts:79
            panel.context.save();
          } else {
            error_dialog(data.message);
          }
        })
        .catch(reason => {
          // The validate_assignment server extension appears to be missing
          error_dialog(`Cannot connect to backend: ${reason}`);
        });
    };
    let button = new ToolbarButton({
      className: 'validate-button',
      // iconClass: 'fa fa-fast-forward',
      label: 'Validate',
      onClick: callback,
      tooltip: 'Validate Assignment'
    });

    let children = panel.toolbar.children();
    let index = 0;
    for (let i = 0; ; i++) {
        let widget = children.next();
        if (widget == undefined) {
            break;
        }
        if (widget.node.classList.contains("jp-Toolbar-spacer")) {
            index = i;
            break;
        }
    }
    panel.toolbar.insertItem(index, 'runAll', button);
    return new DisposableDelegate(() => {
      button.dispose();
    });
  }
}

/**
 * Initialization data for the validate_assignment extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'validate-assignment',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension validate-assignment is activated!');
    app.docRegistry.addWidgetExtension('Notebook', new ButtonExtension());
  }
};

export default extension;
