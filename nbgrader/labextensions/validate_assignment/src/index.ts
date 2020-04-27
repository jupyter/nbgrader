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

export
class ButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let callback = () => {
      // examples/notebook/src/commands.ts:79
      panel.context.save();
      // TODO
      // button.title = "Saving...";
      // tests/test-docregistry/src/context.spec.ts:98
      const notebookSaved = (sender: DocumentRegistry.IContext<INotebookModel>,
                             args: DocumentRegistry.SaveState) => {
        if (args == "completed") {
          requestAPI<any>('get_example')
            .then(data => {
              console.log(data);
              showDialog({
                title: "My Dialog",
                body: JSON.stringify(data),
                buttons: [Dialog.okButton()],
                focusNodeSelector: 'input'
              });
            })
            .catch(reason => {
              // The validate_assignment server extension appears to be missing
              error_dialog(`Cannot connect to backend: ${reason}`);
            });
          // TODO
          /*
          var settings = {
              cache : false,
              data : { path: Jupyter.notebook.notebook_path },
              type : "POST",
              dataType : "json",
              success : function (data, status, xhr) {
                  btn.text('Validate');
                  btn.removeAttr('disabled');
                  validate(data, btn);
              },
              error : function (xhr, status, error) {
                  utils.log_ajax_error(xhr, status, error);
              }
          };
          btn.text('Validating...');
          btn.attr('disabled', 'disabled');
          var url = utils.url_path_join(
              Jupyter.notebook.base_url,
              'assignments',
              'validate'
          );
          ajax(url, settings);
          */
          panel.context.saveState.disconnect(notebookSaved);
        } else if (args == "failed") {
          error_dialog("Cannot save notebook");
          panel.context.saveState.disconnect(notebookSaved);
        }
      };
      panel.context.saveState.connect(notebookSaved);
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
