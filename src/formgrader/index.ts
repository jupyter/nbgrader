import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import {
  ICommandPalette,
  MainAreaWidget,
  WidgetTracker,
  IFrame
} from '@jupyterlab/apputils';

const PLUGIN_ID = "nbgrader/formgrader"
const COMMAND_NAME = "nbgrader:open-formgrader"

class FormgraderWidget extends IFrame {

    app: JupyterFrontEnd;

    constructor(app: JupyterFrontEnd, url:string) {
      super();
      this.referrerPolicy = 'strict-origin-when-cross-origin';
      this.sandbox = ['allow-scripts', 'allow-same-origin', 'allow-forms'];

      this.node.id = "formgrader-iframe"
      this.app = app;

      this.url = url;

      var this_widget = this;

      window.addEventListener('message', function (event) {
        this_widget.on_click(event);
      });

    }

    private on_click(event:MessageEvent){
      var contentWindow = this.node.querySelector('iframe').contentWindow;
      if (contentWindow === event.source){
        var data = JSON.parse(event.data);
        this.app.commands.execute(data.command, data.arguments);
      }
    }
};

/**
 * Initialization data for the formfrader extension.
 */
export const formgrader_extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICommandPalette],
  optional: [ILayoutRestorer],
  activate: async (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    restorer: ILayoutRestorer | null
  )=> {
    console.log('JupyterLab extension formgrader is activated!');

    // Declare a widget variable
    let widget: MainAreaWidget<FormgraderWidget>;

    // Add an application command
    const command: string = COMMAND_NAME;

    // Track the widget state
    let tracker = new WidgetTracker<MainAreaWidget<FormgraderWidget>>({
      namespace: 'nbgrader-formgrader'
    });

    app.commands.addCommand(command,{
    label: 'Formgrader',
    execute: async args => {
      if(!widget || widget.isDisposed){
        const settings = ServerConnection.makeSettings();
        const url = (args.url as string) || URLExt.join(settings.baseUrl, "formgrader");

        const content = new FormgraderWidget(app, url);

        widget = new MainAreaWidget({content});
        widget.id = 'formgrader';
        widget.title.label = 'Formgrader';
        widget.title.closable = true;
        }

        if(!tracker.has(widget)){
        // Track the state of the widget for later restoration
        tracker.add(widget);
        }
        if(!widget.isAttached){
        // Attach the widget to the mainwork area if it's not there
        app.shell.add(widget, 'main');
        }
        widget.content.update();

        // Activate the widget
        app.shell.activateById(widget.id);
      }
    });

    // Add the command to the palette
    palette.addItem({command, category: 'nbgrader'});

    // Restore the widget state
    if (restorer != null){
      restorer.restore(tracker, {
        command,
        name: () => 'nbgrader-formgrader'
      });
    }
  }
};

export default formgrader_extension;