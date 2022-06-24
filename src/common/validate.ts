import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';


const CSS_ERROR_DIALOG = 'nbgrader-ErrorDialog'
const CSS_SUCCESS_DIALOG = 'nbgrader-SuccessDialog'

export function showNbGraderDialog<T>(options: Partial<Dialog.IOptions<T>> = {}, error: boolean = false): Promise<Dialog.IResult<T>> {
  const dialog = new Dialog(options);

  if (error) dialog.addClass(CSS_ERROR_DIALOG);
  else dialog.addClass(CSS_SUCCESS_DIALOG);

  return dialog.launch();
}

export function validate(
  data: { [x: string]: any; value: string; changed: string | any[]; passed: { source: string; }[]; failed: string | any[]; }
  ): boolean {

  var body = document.createElement('div') as HTMLDivElement;
  body.id = 'validation-message';
  var isError = false;
  var success = false;

  if (data.success === true) {
      if (typeof(data.value) === "string") {
          data = JSON.parse(data.value);
      } else {
          data = data.value;
      }
      if (data.type_changed !== undefined) {
        isError = true;
        for (let i=0; i<data.type_changed.length; i++) {
          var div = document.createElement('div')
          var paragraph = document.createElement('p')
          paragraph.innerText = `The following ${data.type_changed[i].old_type} cell has changed to a ${data.type_changed[i].new_type} cell, but it should not have!`;
          div.append(paragraph);
          body.append(div);
          var pre = document.createElement('pre');
          pre.innerText = data.type_changed[i].source;
          body.append(pre);
        }
        body.classList.add("validation-type-changed");
      }
      else if (data.changed !== undefined) {
        isError = true;
        for (var i=0; i<data.changed.length; i++) {
          var div = document.createElement('div')
          var paragraph = document.createElement('p')
          paragraph.innerText = 'The source of the following cell has changed, but it should not have!';
          div.append(paragraph);
          body.append(div);
          var pre = document.createElement('pre');
          pre.innerText = data.changed[i].source;
          body.append(pre);
        }
        body.classList.add("validation-changed");

      } else if (data.passed !== undefined) {
        for (var i=0; i<data.changed.length; i++) {
          var div = document.createElement('div');
          var paragraph = document.createElement('p');
          paragraph.innerText = 'The following cell passed:';
          div.append(paragraph)
          body.append(div)
          var pre = document.createElement('pre');
          pre.innerText = data.passed[i].source;
          body.append(pre);
        }
        body.classList.add("validation-passed");

      } else if (data.failed !== undefined) {
        isError = true;
        for (var i=0; i<data.failed.length; i++) {
          var div = document.createElement('div');
          var paragraph = document.createElement('p');
          paragraph.innerText = 'The following cell failed:';
          div.append(paragraph);
          body.append(div);

          const source = document.createElement('div');
          source.classList.add('jp-RenderedText');
          var pre1 = document.createElement('pre');
          pre1.innerText = data.failed[i].source;
          source.append(pre1);
          body.append(source);

          const error = document.createElement('div');
          error.classList.add('jp-RenderedText');
          var pre2 = document.createElement('pre');
          pre2.innerHTML = data.failed[i].error;
          error.append(pre2);

          body.append(error);

        }
        body.classList.add('validation-failed');

      } else {
        var div = document.createElement('div')
        var paragraph  = document.createElement('p')
        paragraph.innerText = 'Success! Your notebook passes all the tests.';
        div.append(paragraph);
        body.append(div);

        body.classList.add("validation-success");
        success = true;
      }

  } else {
    isError = true;
    var div  = document.createElement('div');
    var paragraph = document.createElement('p');
    paragraph.innerText = 'There was an error running the validate command:';
    div.append(paragraph);
    body.append(div);
    var pre = document.createElement('pre');
    pre.innerText = data.value
    body.append(pre);

  }

  let b: Widget;
  b = new Widget({node: body});
  showNbGraderDialog({
    title: "Validation Results",
    body: b,
    buttons: [Dialog.okButton()]
  }, isError);

  return success;
};
