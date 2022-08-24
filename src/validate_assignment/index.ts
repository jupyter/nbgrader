import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  IDisposable, DisposableDelegate
} from '@lumino/disposable';

import {
  ToolbarButton, Dialog
} from '@jupyterlab/apputils';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import { requestAPI } from './validateassignment';

import { showNbGraderDialog, validate } from '../common/validate';

var nbgrader_version = "0.8.0"; // TODO: hardcoded value

const PLUGIN_ID = "nbgrader/validate-assignment"

class ValidateButton extends ToolbarButton {
  private _buttonCallback = this.newButtonCallback();
  private _versionCheckCallback = this.newVersionCheckCallback();
  private _saveCallback = this.newSaveCallback();
  private panel: NotebookPanel;

  constructor(panel: NotebookPanel) {
    super({
      className: 'validate-button',
      // iconClass: 'fa fa-fast-forward',
      label: 'Validate',
      onClick: () => {this.buttonCallback();},
      tooltip: 'Validate Assignment'
    });
    this.panel = panel;
  }

  private get buttonCallback() {
    return this._buttonCallback;
  }

  private get saveCallback() {
    return this._saveCallback;
  }

  private get versionCheckCallback() {
    return this._versionCheckCallback;
  }

  dispose() {
    if (this.isDisposed) {
      return;
    }
    this.panel = null;
    super.dispose()
  }

  private newSaveCallback() {
    return (sender: DocumentRegistry.IContext<INotebookModel>,
            args: DocumentRegistry.SaveState) => {
      if (args !== 'completed' && args !== 'failed') {
        return;
      }

      this.panel.context.saveState.disconnect(this.saveCallback);

      if (args !== "completed") {
        showNbGraderDialog({
          title: "Validation failed",
          body: "Cannot save notebook",
          buttons: [Dialog.okButton()],
          focusNodeSelector: 'input'
        }, true);
        this.setButtonLabel();
        this.setButtonDisabled(false);
        return;
      }

      this.setButtonLabel('Validating...');
      const notebook_path = this.panel.context.path
      requestAPI<any>(
          'assignments/validate',
          { method: 'POST' },
          new Map([['path', notebook_path]])
      ).then(data => {
        validate(data);
        this.setButtonLabel();
        this.setButtonDisabled(false);
      }).catch(reason => {
        showNbGraderDialog({
          title: "Validation failed",
          body: `Cannot validate: ${reason}`,
          buttons: [Dialog.okButton()],
          focusNodeSelector: 'input'
        }, true);
        this.setButtonLabel();
        this.setButtonDisabled(false);
      });
    }
  }

  private newVersionCheckCallback() {
    return (data: any) => {
      if (data.success !== true) {
        showNbGraderDialog({
          title: "Version Mismatch",
          body: data.message,
          buttons: [Dialog.okButton()],
          focusNodeSelector: 'input'
        }, true);
        return;
      }

      // tests/test-docregistry/src/context.spec.ts:98
      this.setButtonDisabled();
      this.setButtonLabel('Saving...');
      this.panel.context.saveState.connect(this.saveCallback);
      // examples/notebook/src/commands.ts:79
      this.panel.context.save();
    }
  }

  private newButtonCallback() {
    return () => {
      requestAPI<any>(
          'nbgrader_version',
          undefined,
          new Map([['version', nbgrader_version]])
      ).then(
          this.versionCheckCallback
      ).catch(reason => {
        // The validate_assignment server extension appears to be missing
        showNbGraderDialog({
          title: "Validation failed",
          body: `Cannot check version: ${reason}`,
          buttons: [Dialog.okButton()],
          focusNodeSelector: 'input'
        }, true);
      });
    }
  }

  private setButtonDisabled(disabled: boolean = true): void {
    const button = this.node.getElementsByTagName('button')[0];
    if (disabled) {
      button.setAttribute('disabled', 'disabled');
    } else {
      button.removeAttribute('disabled');
    }
  }

  private setButtonLabel(label: string = 'Validate'): void {
    const labelElement = this.node.getElementsByClassName(
        'jp-ToolbarButtonComponent-label')[0] as HTMLElement;
    labelElement.innerText = label;
  }

}

export class ButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    const button = new ValidateButton(panel);

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
export const validate_assignment_extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension validate-assignment is activated!');
    app.docRegistry.addWidgetExtension('Notebook', new ButtonExtension());
  }
};

export default validate_assignment_extension;
