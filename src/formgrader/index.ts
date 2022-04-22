import {
  ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IFileBrowserFactory } from '@jupyterlab/filebrowser';

import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import {
  ICommandPalette, MainAreaWidget, WidgetTracker, IFrame
} from '@jupyterlab/apputils';


class FormgraderWidget extends IFrame {

    app: JupyterFrontEnd;
    browser: IFileBrowserFactory;

    constructor(app: JupyterFrontEnd, browser: IFileBrowserFactory) {
      super();
      this.referrerPolicy = 'strict-origin-when-cross-origin';
      this.sandbox = ['allow-scripts', 'allow-same-origin'];
      this.node.id = "formgrader-iframe"
      this.app = app;
      this.browser = browser;
      var endPoint = "formgrader";

      const settings = ServerConnection.makeSettings();
      const requestURL = URLExt.join(
        settings.baseUrl,
        endPoint
      );

      this.url = requestURL;

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
  id: 'formgrader',
  autoStart: true,
  requires: [ICommandPalette, ILayoutRestorer, IFileBrowserFactory],
  activate: async (app: JupyterFrontEnd, palette: ICommandPalette, restorer: ILayoutRestorer, browser: IFileBrowserFactory)=> {
    console.log('JupyterLab extension formgrader is activated!');

    // Declare a widget variable
    let widget: MainAreaWidget<FormgraderWidget>;

    // Add an application command
    const command: string = 'formgrader:open';

    app.commands.addCommand(command,{
    label: 'Formgrader',
    execute: () => {
        if(!widget){
        const content = new FormgraderWidget(app, browser);
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

    // Track and restore the widget state
    let tracker = new WidgetTracker<MainAreaWidget<FormgraderWidget>>({
      namespace: 'formgrader'
    });
    restorer.restore(tracker, {
      command,
      name: () => 'nbgrader_formgrader'
    });
  }
};

export default formgrader_extension;