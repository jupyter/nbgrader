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

import {
  Widget
} from '@lumino/widgets';

import { requestAPI } from './validateassignment';

function error_dialog(body: string, title: string = 'Validation failed'): void {
  showDialog({
    title: title,
    body: body,
    buttons: [Dialog.okButton()],
    focusNodeSelector: 'input'
  });
}

var nbgrader_version = "0.7.0.dev"; // TODO: hardcoded value

export
class ButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  private button: ToolbarButton;

  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let callback = () => {
      requestAPI<any>('nbgrader_version', undefined, new Map([['version', nbgrader_version]]))
        .then(data => {
          if (data.success) {
            // tests/test-docregistry/src/context.spec.ts:98
            this.setButtonDisabled();
            this.setButtonLabel('Saving...');
            const notebookSaved = (
              sender: DocumentRegistry.IContext<INotebookModel>,
              args: DocumentRegistry.SaveState) => {
              if (args == "completed") {
                panel.context.saveState.disconnect(notebookSaved);
                this.setButtonLabel('Validating...');
                const notebook_path = panel.context.path
                requestAPI<any>('assignments/validate',
                  { method: 'POST' },
                  new Map([['path', notebook_path]]) )
                  .then(data => {
                    this.validate(data);
                    this.setButtonLabel();
                    this.setButtonDisabled(false);
                  })
                  .catch(reason => {
                    error_dialog(`Cannot validate: ${reason}`);
                    this.setButtonLabel();
                    this.setButtonDisabled(false);
                  });
              } else if (args == "failed") {
                panel.context.saveState.disconnect(notebookSaved);
                error_dialog("Cannot save notebook");
                this.setButtonLabel();
                this.setButtonDisabled(false);
              }
            };
            panel.context.saveState.connect(notebookSaved);
            // examples/notebook/src/commands.ts:79
            panel.context.save();
          } else {
            error_dialog(data.message, 'Version Mismatch');
          }
        })
        .catch(reason => {
          // The validate_assignment server extension appears to be missing
          error_dialog(`Cannot check version: ${reason}`);
        });
    };
    let button = new ToolbarButton({
      className: 'validate-button',
      // iconClass: 'fa fa-fast-forward',
      label: 'Validate',
      onClick: callback,
      tooltip: 'Validate Assignment'
    });
    this.button = button

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

  private setButtonDisabled(disabled: boolean = true): void {
    const button = this.button.node.getElementsByTagName('button')[0];
    if (disabled) {
      button.setAttribute('disabled', 'disabled');
    } else {
      button.removeAttribute('disabled');
    }
  }

  private setButtonLabel(label: string = 'Validate'): void {
    const labelElement = this.button.node.getElementsByClassName(
        'jp-ToolbarButtonComponent-label')[0] as HTMLElement;
    labelElement.innerText = label;
  }

  private validate(data: any): void {
    let body = document.createElement('div');
    body.id = "validation-message";

    const newSourceBox = function(text: string): HTMLDivElement {
      const source = document.createElement('div');
      const sourceText = document.createElement('pre');
      sourceText.innerText = text;
      source.appendChild(sourceText);
      source.classList.add('jp-InputArea-editor');
      return source;
    };

    const newTextBox = function(text: string): HTMLDivElement {
      const container = document.createElement('div');
      const paragraph = document.createElement('p');
      paragraph.innerText = text;
      container.appendChild(paragraph);
      return container;
    };

    if (data.success === true) {
      if (typeof(data.value) === "string") {
        data = JSON.parse(data.value);
      } else {
        data = data.value;
      }
      if (data.type_changed !== undefined) {
        for (let i=0; i<data.type_changed.length; i++) {
          const textBox = newTextBox(`The following ${data.type_changed[i].old_type} cell has changed to a ${data.type_changed[i].new_type} cell, but it should not have!`);
          const source = newSourceBox(data.type_changed[i].source);
          body.appendChild(textBox);
          body.appendChild(source);
        }
        body.classList.add("validation-type-changed");

      } else if (data.changed !== undefined) {
        for (let i=0; i<data.changed.length; i++) {
          const textBox = newTextBox('The source of the following cell has changed, but it should not have!');
          const source = newSourceBox(data.changed[i].source);
          body.appendChild(textBox);
          body.appendChild(source);
        }
        body.classList.add("validation-changed");

      } else if (data.passed !== undefined) {
        for (let i=0; i<data.changed.length; i++) {
          const textBox = newTextBox('The following cell passed:');
          const source = newSourceBox(data.passed[i].source);
          body.appendChild(textBox);
          body.appendChild(source);
        }
        body.classList.add("validation-passed");

      } else if (data.failed !== undefined) {
        for (let i=0; i<data.failed.length; i++) {
          const textBox = newTextBox('The following cell failed:');
          const source = newSourceBox(data.failed[i].source);
          const error = document.createElement('div');
          const errorText = document.createElement('pre');
          errorText.innerHTML = data.failed[i].error;
          error.classList.add('jp-RenderedText');
          error.setAttribute('data-mime-type', 'application/vnd.jupyter.stderr');
          error.appendChild(errorText);
          body.appendChild(textBox);
          body.appendChild(source);
          body.appendChild(error);
        }
        body.classList.add("validation-failed");

      } else {
        const textBox = newTextBox('Success! Your notebook passes all the tests.');
        body.appendChild(textBox);
        body.classList.add("validation-success");
      }

    } else {
      const textBox = newTextBox('There was an error running the validate command:');
      const source = document.createElement('pre');
      source.innerText = data.value;
      body.appendChild(textBox);
      body.appendChild(source);
    }

    showDialog({
      title: "Validation Results",
      body: new Widget({node: body}),
      buttons: [Dialog.okButton()],
      focusNodeSelector: 'input'
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
