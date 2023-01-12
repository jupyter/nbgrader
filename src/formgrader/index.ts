import { JupyterFrontEnd } from '@jupyterlab/application';

import { IFrame } from '@jupyterlab/apputils';

export class FormgraderWidget extends IFrame {

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
        this_widget.on_message(event);
      });

    }

    private on_message(event:MessageEvent){
      var contentWindow = this.node.querySelector('iframe').contentWindow;
      if (contentWindow === event.source){
        var data = JSON.parse(event.data);
        this.app.commands.execute(data.command, data.arguments);
      }
    }
};
