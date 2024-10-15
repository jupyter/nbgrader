import { JupyterFrontEnd } from '@jupyterlab/application';

import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import { Dialog } from '@jupyterlab/apputils';

import { Widget } from '@lumino/widgets';

import { PageConfig } from '@jupyterlab/coreutils';

import * as React from 'react';

import { showNbGraderDialog, validate } from '../common/validate';

export class AssignmentList {

  released_selector: string;
  fetched_selector: string;
  submitted_selector: string;
  released_element: HTMLDivElement;
  fetched_element: HTMLDivElement;
  submitted_element: HTMLDivElement;
  options: Map<string, string>;
  base_url: string;
  app: JupyterFrontEnd;
  callback: () => void;

  list_loading_ids = ['released_assignments_list_loading','fetched_assignments_list_loading','submitted_assignments_list_loading'];
  list_placeholder_ids = ['released_assignments_list_placeholder','fetched_assignments_list_placeholder', 'submitted_assignments_list_placeholder'];
  list_error_ids = ['released_assignments_list_error','fetched_assignments_list_error', 'submitted_assignments_list_error'];

  constructor(widget: Widget, released_selector: string, fetched_selector: string, submitted_selector: string, options: Map<string, string>, app:JupyterFrontEnd){
    this.released_selector = released_selector;
    this.fetched_selector = fetched_selector;
    this.submitted_selector = submitted_selector;

    var div_elements = widget.node.getElementsByTagName('div');
    this.released_element = div_elements.namedItem(released_selector);
    this.fetched_element = div_elements.namedItem(fetched_selector);
    this.submitted_element = div_elements.namedItem(submitted_selector);

    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();

    this.app = app;
    this.callback = undefined;

  }

  public clear_list(loading: boolean): void {
    var elems = [this.released_element, this.fetched_element, this.submitted_element];
    var i;
    var j;

    // remove list items
    for (i = 0; i < elems.length; i++) {

      for(j =0; j < elems[i].children.length; ++j){
        if(elems[i].children[j].classList.contains('list_item')){
          elems[i].removeChild(elems[i].children[j]);
          --j;
        }

      }

      if (loading) {
          // show loading
          (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = false;

          // hide placeholders and errors
          (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = true;
          (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = true;

      } else {
          // show placeholders display
          (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = false;

          // hide loading and errors
          (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = true;
          (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = true;

      }
    }
  };

  private load_list_success(data: string | any[]): void {
    this.clear_list(false);

    var len = data.length;
    for (var i=0; i<len; i++) {
        var element = document.createElement('div');
        new Assignment(element, data[i], this.fetched_selector,
          (newData)=>{this.handle_load_list(newData)}, this.options, this.app);
        if (data[i].status === 'released') {
          this.released_element.append(element);
          (<HTMLDivElement>this.released_element.children.namedItem('released_assignments_list_placeholder')).hidden = true;
        } else if (data[i]['status'] === 'fetched') {
          this.fetched_element.append(element);
          (<HTMLDivElement>this.fetched_element.children.namedItem('fetched_assignments_list_placeholder')).hidden = true;
        } else if (data[i]['status'] === 'submitted') {
          this.submitted_element.append(element);
          (<HTMLDivElement>this.submitted_element.children.namedItem('submitted_assignments_list_placeholder')).hidden = true;
        }
    }

    var assignments  = this.fetched_element.getElementsByClassName('assignment-notebooks-link');
    for(let a of assignments){
      var icon = document.createElement('i');
      icon.classList.add('fa', 'fa-caret-right');
      a.append(icon);
      (<HTMLAnchorElement>a).onclick = function(event){

        if(a.children[0].classList.contains('fa-caret-right')){
          a.children[0].classList.remove('fa-caret-right');
          a.children[0].classList.add('fa-caret-down');
        }else{
          a.children[0].classList.remove('fa-caret-down');
          a.children[0].classList.add('fa-caret-right');
        }

        /* Open or close collapsed child list on click */
        const list_item = (<HTMLAnchorElement>event.target).closest('.list_item');
        list_item.querySelector('.collapse').classList.toggle('in');
      }

    }

    if (this.callback) {
      this.callback();
      this.callback = undefined;
    }


  };

  public show_error(error: string): void {
    var elems = [this.released_element, this.fetched_element, this.submitted_element];
    var i;

    // remove list items
    for (i = 0; i < elems.length; i++) {
      for(var j =0; j < elems[i].children.length; ++j){
        if(elems[i].children[j].classList.contains('list_item')){
          elems[i].removeChild(elems[i].children[j]);
          --j;
        }

      }

      // show errors
      (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = false;
      (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).innerText = error;

      // hide loading and placeholding
      (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = true;
      (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = true;
    }
  };

  public handle_load_list(data: { success: any; value: any; }): void {
    if (data.success) {
        this.load_list_success(data.value);
    } else {
      this.show_error(data.value);
    }
  };

  public async load_list(course: string, callback: any){
    this.callback = callback;
    this.clear_list(true);
    try {
      const data = await requestAPI<any>('assignments?course_id=' + course, {
        method: 'GET',
      });
      this.handle_load_list(data)
    } catch (reason) {
      console.error(`Error on GET /assignments.\n${reason}`);
    }

  };


};

class Assignment {
  element: HTMLDivElement;
  data: any;
  parent: string;
  on_refresh: (data: any) => void;
  options: Map<string, string>;
  base_url: any;
  app: JupyterFrontEnd;

  constructor(element: HTMLDivElement , data: any, parent: string , on_refresh: (data: any) => void, options: Map<string, string>, app: JupyterFrontEnd){
    this.element = element;
    this.data = data;
    this.parent = parent;
    this.on_refresh = on_refresh;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.app = app;
    this.style();
    this.make_row();
  }

  private style(): void {
    this.element.classList.add('list_item', "row");
  };

  private escape_id(): string {
    // construct the id from the course id and the assignment id, and also
    // prepend the id with "nbgrader" (this also ensures that the first
    // character is always a letter, as required by HTML 4)
    var id = "nbgrader-" + this.data['course_id'] + "-" + this.data['assignment_id'];

    // replace spaces with '_'
    id = id.replace(/ /g, "_");

    // remove any characters that are invalid in HTML div ids
    id = id.replace(/[^A-Za-z0-9\-_]/g, "");

    return id;
  };

  private make_link(): HTMLSpanElement {
    var container = document.createElement('span');;
    container.classList.add('item_name', 'col-sm-6');

    var link;
    if (this.data['status'] === 'fetched') {
        link = document.createElement ('a');
        var id = this.escape_id();
        link.classList.add('collapsed', 'assignment-notebooks-link');
        link.setAttribute('role', 'button');
        link.setAttribute('data-toggle', 'collapse');
        link.setAttribute('data-parent', this.parent);
        link.setAttribute('href', '#' + id);
        link.setAttribute('aria-expanded', 'false');
        link.setAttribute('aria-controls', id);
    }else{
      link = document.createElement('span');
    }
    link.innerText = (this.data['assignment_id']);
    container.append(link);
    return container;
  };

  private submit_error(data: { value: any; }): void {

    const body_title = React.createElement('p', null, 'Assignment not submitted:');
    const body_content = React.createElement('pre', null, data.value);
    const body = React.createElement("div", {'id': 'submission-message'}, [body_title, body_content]);

    showNbGraderDialog({
      title: "Invalid Submission",
      body: body,
      buttons: [Dialog.okButton()]
    }, true);


  };

  private make_button(): HTMLSpanElement{
    var container = document.createElement('span');
    container.classList.add('item_status', 'col-sm-4')
    var button = document.createElement('button');
    button.classList.add('btn', 'btn-primary', 'btn-xs')
    container.append(button);
    var that = this;
    if (this.data['status'] === 'released') {

      button.innerText = "Fetch";
      button.onclick = async function(){
        button.innerText = 'Fetching...';
        button.setAttribute('disabled', 'disabled');
        const dataToSend = { 'course_id': that.data['course_id'], 'assignment_id': that.data['assignment_id']};
        try {
          const reply = await requestAPI<any>('assignments/fetch', {
            body: JSON.stringify(dataToSend),
            method: 'POST'
          });

          that.on_refresh(reply);
        } catch (reason) {
          remove_children(container);
          container.innerText = 'Error fetching assignment.';
          console.error(
            `Error on POST /assignment_list/fetch ${dataToSend}.\n${reason}`
          );
        }

      }
    } else if (this.data.status == 'fetched') {
        var refetchButton = document.createElement('button');
        refetchButton.classList.add('btn', 'btn-danger', 'btn-xs');
        refetchButton.setAttribute('data-bs-toggle', 'tooltip');
        refetchButton.setAttribute('data-bs-placement', 'top');
        refetchButton.setAttribute('style', 'background:#d43f3a; margin-left:5px');
        refetchButton.setAttribute('title', 'If you broke any of your assignment files and you want to redownload them, delete those files and click this button to refetch the original version of those files.')
        container.append(refetchButton);
        
        refetchButton.innerText = 'Refetch';
        refetchButton.onclick = async function(){
          refetchButton.innerText = 'Refetching...';
          refetchButton.setAttribute('disabled', 'disabled');
          const dataToSend = { course_id: that.data['course_id'], assignment_id: that.data['assignment_id']};
          try {
            const reply = await requestAPI<any>('assignments/fetch_missing', {
              body: JSON.stringify(dataToSend),
              method: 'POST'
            });

            that.on_refresh(reply);

          } catch (reason) {
            remove_children(container);
            container.innerText = 'Error refetching assignment.';
            console.error(
              `Error on POST /assignment_list/fetch_missing ${dataToSend}.\n${reason}`
            );
          }
        }

        button.innerText = "Submit";
        button.onclick = async function(){
          button.innerText = 'submitting...';
          button.setAttribute('disabled', 'disabled');
          const dataToSend = { course_id: that.data['course_id'], assignment_id: that.data['assignment_id']};
          try {
            const reply = await requestAPI<any>('assignments/submit', {
              body: JSON.stringify(dataToSend),
              method: 'POST'
            });

            if(!reply.success){
              that.submit_error(reply);
              button.innerText = 'Submit'
              button.removeAttribute('disabled')
            }else{
              that.on_refresh(reply);
            }

          } catch (reason) {
            remove_children(container);
            container.innerText = 'Error submitting assignment.';
            console.error(
              `Error on POST /assignment_list/assignments/submit ${dataToSend}.\n${reason}`
            );
          }

        }


    } else if (this.data.status == 'submitted') {
      button.innerText = "Fetch Feedback";
      button.onclick = async function(){
        button.innerText = 'Fetching Feedback...';
        button.setAttribute('disabled', 'disabled');
        const dataToSend = { course_id: that.data['course_id'], assignment_id: that.data['assignment_id']};
        try {
          const reply = await requestAPI<any>('assignments/fetch_feedback', {
            body: JSON.stringify(dataToSend),
            method: 'POST'
          });

          that.on_refresh(reply);

        } catch (reason) {
          remove_children(container);
          container.innerText = 'Error fetching feedback.';
          console.error(
            `Error on POST /assignments/fetch_feedback ${dataToSend}.\n${reason}`
          );
        }

      }
    }

    return container;
  };

  private make_row(): void {
    var row = document.createElement('div');
    row.classList.add('col-md-12');
    var link = this.make_link();
    row.append(link);
    var s = document.createElement('span');
    s.classList.add('item_course', 'col-sm-2')
    s.innerText = this.data['course_id']
    row.append(s)

    var id, element;
    var children = document.createElement('div');
    if (this.data['status'] == 'submitted') {
      id = this.escape_id() + '-submissions';
      children.id = id;
      children.classList.add('panel-collapse', 'list_container', 'assignment-notebooks');
      children.setAttribute('role', 'tabpanel');

      var d = document.createElement('div');
      d.classList.add('list_item', 'row');
      children.append(d);
      for (var i=0; i<this.data['submissions'].length; i++) {
        element = document.createElement('div');
        new Submission(element, this.data.submissions[i], this.options, this.app);
        children.append(element);
      }

    } else if (this.data['status'] === 'fetched') {

        id = this.escape_id();
        children.id = id;
        children.classList.add('panel-collapse', 'list_container', 'assignment-notebooks', 'collapse');
        children.setAttribute('role', 'tabpanel');
        var d = document.createElement('div');
        d.classList.add('list_item', 'row');
        children.append(d);
        for (var i=0; i<this.data['notebooks'].length; i++) {
            element = document.createElement('div');
            this.data.notebooks[i]['course_id'] = this.data['course_id'];
            this.data.notebooks[i]['assignment_id'] = this.data['assignment_id'];
            new Notebook(element, this.data.notebooks[i], this.options, this.app);
            children.append(element);
        }
    }

    row.append(this.make_button());
    this.element.innerHTML= ''

    this.element.append(row);
    this.element.append(children);
  };

};

const remove_children = function (element: HTMLElement) {
  element.innerHTML = '';
}

class Submission{

  element: any;
  data: any;
  options: Map<string, string>;
  base_url: any;
  app: JupyterFrontEnd;

  constructor(element: HTMLDivElement, data: any, options: Map<string, string>, app: JupyterFrontEnd){
    this.element = element;
    this.data = data;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.app = app
    this.style();
    this.make_row();

  }

  private style(): void {
    this.element.classList.add('list_item', 'row', 'nested_list_item');
  };

  private make_row(): void{
    var container = document.createElement('div')
    container.classList.add('col-md-12');
    var status = document.createElement('span')
    status.classList.add('item_name', 'col-sm-6');
    var s = document.createElement('span').innerText = this.data['timestamp'];
    status.append(s);


    if (this.data['has_local_feedback'] && !this.data['feedback_updated']) {
      var app = this.app;
      var feedback_path = this.data['local_feedback_path'];
      // var url = URLExt.join(this.base_url, 'tree', this.data['local_feedback_path']);
      var link = document.createElement('a')
      link.onclick = function() {
        app.commands.execute('filebrowser:go-to-path', {
          path: feedback_path
        });
      }
      link.innerText = ' (view feedback)';
      status.append(link);
    } else if (this.data['has_exchange_feedback']) {
      var feedback = document.createElement('span');
      feedback.innerText = ' (feedback available to fetch)';
      status.append(feedback);
    } else {
      var feedback = document.createElement('span');
      feedback.innerText = '';
      status.append(feedback);
    }
    container.append(status);
    var s1 = document.createElement('span');
    s1.classList.add('item_course', 'col-sm-2')
    container.append(s1);
    var s2 = document.createElement('span');
    s2.classList.add('item_status', 'col-sm-4')
    container.append(s2);
    this.element.append(container);
  };
};

class Notebook{
  element: HTMLDivElement;
  data: any;
  options: Map<string, string>;
  base_url: any;
  app: JupyterFrontEnd;

  constructor (element: HTMLDivElement, data: any, options: Map<string, string>, app:JupyterFrontEnd) {
    this.element = element;
    this.data = data;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.app = app;
    this.style();
    this.make_row();

  }

  private style(): void  {
    this.element.classList.add('list_item', 'row', 'nested_list_item');
  };

  private make_button(): HTMLSpanElement {
    var that = this;
    var container = document.createElement('span');
    container.classList.add('item_status', 'col-sm-4');
    var button = document.createElement('button')
    button.classList.add('btn', 'btn-default', 'btn-xs')

    container.append(button);

    button.innerText = 'Validate';
    button.onclick = async function(){
      button.innerText = 'Validating...';
      button.setAttribute('disabled', 'disabled');
      const dataToSend = { path: that.data['path']}
      try {
        const reply = await requestAPI<any>('assignments/validate', {
          body: JSON.stringify(dataToSend),
          method: 'POST'
        });

        button.innerText = 'Validate'
        button.removeAttribute('disabled')
        const success = validate(reply);

        if (success) that.validate_success(button);
        else that.validate_failure(button);

      } catch (reason) {
        remove_children(container);
        container.innerText = 'Error validating assignment.';
        console.error(
          `Error on POST /assignments/validate ${dataToSend}.\n${reason}`
        );
      }
    }

    return container;
  };

  private validate_success(button: HTMLButtonElement): void {
    button.classList.remove('btn-default', 'btn-danger', 'btn-success');
    button.classList.add('btn-success');
  };

  private validate_failure(button: HTMLButtonElement): void {
    button.classList.remove('btn-default', 'btn-danger', 'btn-success');
    button.classList.add("btn-danger");
  };

  private make_row(): void {

    var app = this.app;
    var nb_path = this.data['path']

    var container = document.createElement('div');
    container.classList.add('col-md-12');
    var s1 = document.createElement('span');
    s1.classList.add('item_name', 'col-sm-6');

    var a = document.createElement('a');
    a.href = '#';
    a.innerText = this.data['notebook_id'];
    a.onclick = function() {
      app.commands.execute('docmanager:open', {
        path: nb_path
      });
    }

    s1.append(a);

    container.append(s1);
    var s2 = document.createElement('span');
    s2.classList.add('item_course', 'col-sm-2');
    container.append(s2);
    container.append(this.make_button());
    this.element.append(container);
  };
};

export class CourseList{
  course_list_selector: string;
  default_course_selector: string;
  dropdown_selector: string;
  refresh_selector: string;
  assignment_list: AssignmentList;
  current_course: string;
  options = new Map();
  base_url: string;
  data : string[];
  course_list_element : HTMLUListElement;
  default_course_element: HTMLButtonElement;
  dropdown_element: HTMLButtonElement;
  refresh_element: HTMLButtonElement;

  constructor(widget: Widget, course_list_selector: string, default_course_selector: string, dropdown_selector: string, refresh_selector: string, assignment_list: AssignmentList, options: Map<string, string>) {

  this.course_list_selector = course_list_selector;
  this.default_course_selector = default_course_selector;
  this.dropdown_selector = dropdown_selector;
  this.refresh_selector = refresh_selector;
  this.course_list_element = widget.node.getElementsByTagName('ul').namedItem(course_list_selector);
  var buttons = widget.node.getElementsByTagName('button');
  this.default_course_element = buttons.namedItem(default_course_selector);
  this.dropdown_element = buttons.namedItem(dropdown_selector);
  this.refresh_element = buttons.namedItem(refresh_selector);

  this.assignment_list = assignment_list;
  this.current_course = undefined;

  //options = options || {};
  this.options = options;
  this.base_url = options.get('base_url') || PageConfig.getBaseUrl();

  this.data = undefined;

  var that = this;

  /* Open the dropdown course_list when clicking on dropdown toggle button */
  this.dropdown_element.onclick = function() {
    that.course_list_element.classList.toggle('open');
  }

  /* Close the dropdown course_list if clicking anywhere else */
  document.onclick = function(event) {
    if ((<HTMLElement>event.target).closest('button') != that.dropdown_element) {
      that.course_list_element.classList.remove('open');
    }
  }

  this.refresh_element.onclick = function(){
    that.load_list();
  }
  this.bind_events()
}

private enable_list(): void {
  this.dropdown_element.removeAttribute("disabled");
};

private disable_list(): void {
  this.dropdown_element.setAttribute("disabled", "disabled");
};

public clear_list(): void {
  // remove list items
  if(this.course_list_element.children.length > 0){
    this.course_list_element.innerHTML = '';
  }
};

private bind_events(): void {
  this.refresh_element.click();
};

private async load_list() {
  this.disable_list()
  this.clear_list();
  this.assignment_list.clear_list(true);

  try {
    const data = await requestAPI<any>('courses');
    this.handle_load_list(data)
  } catch (reason) {
    console.error(`Error on GET /courses.\n${reason}`);
  }

};

private handle_load_list(data: { success: any; value: any; }): void {
  if (data.success) {
      this.load_list_success(data.value);
  } else {
      this.default_course_element.innerText = "Error fetching courses!";
      this.enable_list();
      this.assignment_list.show_error(data.value);
  }
};

private load_list_success(data: string[]): void {
  this.data = data;
  this.disable_list()
  this.clear_list();

  if (this.data.length === 0) {
      this.default_course_element.innerText = "No courses found.";
      this.assignment_list.clear_list(false);
      this.enable_list()
      return;
  }

  if (!this.data.includes(this.current_course)) {
      this.current_course = undefined;
  }

  if (this.current_course === undefined) {
      this.change_course(this.data[0]);
  } else {
      // we still want to "change" the course here to update the
      // assignment list
      this.change_course(this.current_course);
  }
};

private change_course(course: string): void {
  this.disable_list();
  if (this.current_course !== undefined) {
      this.default_course_element.innerText = course;
  }
  this.current_course = course;
  this.default_course_element.innerText = this.current_course;
  var success = ()=>{this.load_assignment_list_success()};
  this.assignment_list.load_list(course, success);
};

private load_assignment_list_success(): void {
  if (this.data) {
      var that = this;
      var set_course = function (course: string) {
          return function () { that.change_course(course); };
      }

      for (var i=0; i<this.data.length; i++) {
        var a = document.createElement('a');
        a.href = '#';
        a.innerText = this.data[i];
        var element = document.createElement('li');
        element.append(a);
        element.onclick = set_course(this.data[i]);
        this.course_list_element.append(element);
      }
      this.data = undefined;
  }
  this.enable_list();
};

}

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
  endPoint = '',
  init: RequestInit = {}
): Promise<T> {
  // Make request to Jupyter API
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(
    settings.baseUrl,
    // 'assignment_list', // API Namespace
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error as TypeError);
  }

  const data = await response.json();

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message);
  }

  return data;
}
