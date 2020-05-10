import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import { Dialog, showDialog } from '@jupyterlab/apputils';

import { Widget } from '@lumino/widgets';

import { PageConfig } from '@jupyterlab/coreutils';


export class AssignmentList{
  released_selector: string;
  fetched_selector: string;
  submitted_selector: string;
  released_element: HTMLDivElement;
  fetched_element: HTMLDivElement;
  submitted_element: HTMLDivElement;
  options: Map<string, string>;
  base_url: string;
  callback: () => void;
  clear_list: (loading: any) => void;
  load_list: (course: string, callback: any) => void;
  load_list_success: (data: any) => void;
  handle_load_list: (data: any) => void;
  show_error: (error: any) => void;

  // FIX ME consider using query selector instead!!
  list_loading_ids = ['released_assignments_list_loading','fetched_assignments_list_loading','submitted_assignments_list_loading'];
  list_placeholder_ids = ['released_assignments_list_placeholder','fetched_assignments_list_placeholder', 'submitted_assignments_list_placeholder'];
  list_error_ids = ['released_assignments_list_error','fetched_assignments_list_error', 'submitted_assignments_list_error'];

  constructor(widget: Widget, released_selector: string, fetched_selector: string, submitted_selector: string, options: Map<string, string>){ 
  this.released_selector = released_selector;
  this.fetched_selector = fetched_selector;
  this.submitted_selector = submitted_selector;

  var div_elments = widget.node.getElementsByTagName('div');
  this.released_element = div_elments.namedItem(released_selector);
  this.fetched_element = div_elments.namedItem(fetched_selector);
  this.submitted_element = div_elments.namedItem(submitted_selector);

  //options = options || {};
  this.options = options;
  this.base_url = options.get('base_url') || PageConfig.getBaseUrl();

  this.callback = undefined;

  }
};


AssignmentList.prototype.clear_list = function (loading) {
  var elems = [this.released_element, this.fetched_element, this.submitted_element];
  var i;
  var j;

  // remove list items
  for (i = 0; i < elems.length; i++) {
      
    // FIX ME Consider making function or finding elements by classname and deleting them
    for(j =0; j < elems[i].children.length; ++j){
      if(elems[i].children[j].classList.contains('list_item')){
        elems[i].removeChild(elems[i].children[j]);
        --j;
      }

    }

    if (loading) {
        // show loading
        // FIX ME avoid doing all this casting
        (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = false;
        
        // hide placeholders and errors
        (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = true;
        (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = true;

    } else {
        // show placeholders
        (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = false;

        // hide loading and errors
        (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = true;
        (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = true;
        
    }
  }
};

class Assignment {
  element: HTMLDivElement;
  data: any;
  parent: string;
  on_refresh: (data: any) => void;
  options: Map<string, string>;
  base_url: any;
  style: () => void;
  make_row: () => void;
  make_link: () => any;
  escape_id: () => string;
  make_button: () => any;
  submit_error: (data: any) => void;

  constructor(element: HTMLDivElement , data: any, parent: string , on_refresh: (data: any) => void, options: Map<string, string>){
    this.element = element;
    this.data = data;
    this.parent = parent;
    this.on_refresh = on_refresh;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.style();
    this.make_row();
  }
}; 

Assignment.prototype.style = function () {
  this.element.classList.add('list_item', "row");
};

Assignment.prototype.escape_id = function () {
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
Assignment.prototype.make_link = function () {
  var container = document.createElement('span');;
  container.classList.add('item_name', 'col-sm-6');

  var link;
  if (this.data['status'] === 'fetched') {
      link = document.createElement ('a');
      var id = this.escape_id();
      link.classList.add('collapsed', 'assignment-notebooks-link')
      link.setAttribute('role', 'button')
      link.setAttribute('data-toggle', 'collapse')
      link.setAttribute('data-parent', this.parent)
      link.setAttribute('href', '#' + id)
  }else{
    link = document.createElement('span');
  }
  link.innerText = (this.data['assignment_id']);
  container.append(link);
  return container;
};

Assignment.prototype.submit_error = function (data) {

  showDialog({
    title: "Invalid Submission",
    body: data.value,
    buttons: [Dialog.okButton()]
  });


};

const remove_children = function (element: HTMLElement) {
  element.innerHTML = '';
}


Assignment.prototype.make_button = function () {
  var container = document.createElement('span');
  container.classList.add('item_status', 'col-sm-4')
  var button = document.createElement('button');
  button.classList.add('btn', 'btn-primary', 'btn-xs')
  container.append(button);
  var that = this;
  if (this.data['status'] === 'released') {

    button.innerText = "fetch";
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
        console.log(reply);
      } catch (reason) {
        remove_children(container);
        container.innerText = 'Error fetching assignment.';
        console.error(
          `Error on POST /assignment_list/fetch ${dataToSend}.\n${reason}`
        );
      }
      
    }
  } else if (this.data.status == 'fetched') {
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

          console.log(reply);
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

        console.log(reply);
      } catch (reason) {
        remove_children(container);
        container.innerText = 'Error fetching feedback.';
        console.error(
          `Error on POST /assignment_list/assignments/fetch_feedback ${dataToSend}.\n${reason}`
        );
      }
      
    }
  }

  return container;
};


Assignment.prototype.make_row = function () {
  var row = document.createElement('div');
  row.classList.add('col-md-12');
  var link = this.make_link();
  row.append(link);
  var s = document.createElement('span');
  s.classList.add('item_course', 'col-sm-2')
  s.innerText = this.data['course_id']
  row.append(s)

  var id, element, child;
  var children = document.createElement('div');
  if (this.data['status'] == 'submitted') {
    id = this.escape_id() + '-submissions';
    children.setAttribute('id', id)
    children.classList.add('panel-collapse', 'list_container', 'assignment-notebooks')
    children.setAttribute('role', 'tabpanel')

    var d = document.createElement('div');;
    d.classList.add('list_item', 'row')
    children.append(d);
    for (var i=0; i<this.data['submissions'].length; i++) {
      element = document.createElement('div');
      child = new Submission(element, this.data.submissions[i], this.options);
      console.log(child.base_url);
      children.append(element);
    }

  } else if (this.data['status'] === 'fetched') {
      link.onclick = function(){
        if(children.classList.contains('in')){
          children.classList.remove('in');
        }else{
          children.classList.add('in');

        }
      };
      id = this.escape_id();
      children.setAttribute('id', id);
      children.classList.add('panel-collapse', 'list_container', 'assignment-notebooks', 'collapse'); 
      children.setAttribute('role', 'tabpanel');
      var d = document.createElement('div');
      d.classList.add('list_item', 'row');
      children.append(d);
      for (var i=0; i<this.data['notebooks'].length; i++) {
          element = document.createElement('div');
          this.data.notebooks[i]['course_id'] = this.data['course_id'];
          this.data.notebooks[i]['assignment_id'] = this.data['assignment_id'];
          child = new Notebook(element, this.data.notebooks[i], this.options);
          children.append(element);
      }
  }

  row.append(this.make_button());
  this.element.innerHTML= ''

  this.element.append(row);
  this.element.append(children);
};

AssignmentList.prototype.load_list_success = function (data) {
  this.clear_list(false);

  var len = data.length;
  for (var i=0; i<len; i++) {
      var element = document.createElement('div');
      var item = new Assignment(element, data[i], this.fetched_selector,
        (newData)=>{this.handle_load_list(newData)}, this.options);
      console.log(item.base_url)
      if (data[i].status === 'released') {
        this.released_element.append(element);
        (<HTMLDivElement>this.released_element.children.namedItem('released_assignments_list_placeholder')).hidden = true
      } else if (data[i]['status'] === 'fetched') {
        this.fetched_element.append(element);
        (<HTMLDivElement>this.fetched_element.children.namedItem('fetched_assignments_list_placeholder')).hidden = true
      } else if (data[i]['status'] === 'submitted') {
        this.submitted_element.append(element);
        (<HTMLDivElement>this.submitted_element.children.namedItem('submitted_assignments_list_placeholder')).hidden = true
      }
  }

  var assignments  = this.fetched_element.getElementsByClassName('assignment-notebooks-link');
  for(let a of assignments){
    var icon = document.createElement('i');
    icon.classList.add('fa', 'fa-caret-right');
    a.append(icon);
    (<HTMLAnchorElement>a).onclick = function(){
      if(icon.classList.contains('fa-caret-right')){
        icon.classList.remove('fa-caret-right');
        icon.classList.add('fa-caret-down');
      }else{
        icon.classList.remove('fa-caret-down');
        icon.classList.add('fa-caret-right');
      }

    }
    
    
  }
  if (this.callback) {
    this.callback();
    this.callback = undefined;
  }


};

AssignmentList.prototype.show_error = function (error) {
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
    // FIX ME avoid doing all this casting
    (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).hidden = false;
    (<HTMLDivElement>elems[i].children.namedItem(this.list_error_ids[i])).innerText = error;

    // hide loading and placeholding
    (<HTMLDivElement>elems[i].children.namedItem(this.list_loading_ids[i])).hidden = true;
    (<HTMLDivElement>elems[i].children.namedItem(this.list_placeholder_ids[i])).hidden = true;
  }
};

AssignmentList.prototype.handle_load_list = function (data) {
  if (data.success) {
      this.load_list_success(data.value);
  } else {
    this.show_error(data.value); 
  }
};


AssignmentList.prototype.load_list = async function (course: string, callback: any) {
  this.callback = callback;
  this.clear_list(true);
  try {
    const data = await requestAPI<any>('assignments?course_id=' + course, { 
      method: 'GET', // FIX ME NEED TO PASS IN THE COURSE ID
    });
    console.log(data);
    this.handle_load_list(data)
  } catch (reason) {
    console.error(`Error on GET /assignment_list/assignments.\n${reason}`);
  }

};

class Submission{
  style: () => void;
  make_row: () => void;
  element: any;
  data: any;
  options: Map<string, string>;
  base_url: any;
  
  constructor(element: HTMLDivElement, data: any, options: Map<string, string>){ 
    this.element = element;
    this.data = data;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.style();
    this.make_row();

  }
};

Submission.prototype.style = function () {
  this.element.classList.add('list_item');
  this.element.classList.add('row');
};

Submission.prototype.make_row = function () {
  var container = document.createElement('div')
  container.classList.add('col-md-12');
  var status = document.createElement('span')
  status.classList.add('item_name', 'col-sm-6');
  var s = document.createElement('span').innerText = this.data['timestamp'];
  status.append(s);


  if (this.data['has_local_feedback'] && !this.data['feedback_updated']) {
    var url = URLExt.join(this.base_url, 'tree', this.data['local_feedback_path']);
    var link = document.createElement('a')
    link.setAttribute('href', url);
    link.setAttribute('target', '_blank');
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

class Notebook{
  style: () => void;
  make_row: () => void;
  element: HTMLDivElement;
  data: any;
  options: Map<string, string>;
  base_url: any;
  make_button: () => any;
  validate: (data: any, button: any) => void;
  validate_success: (button: HTMLButtonElement) => void;
  validate_failure: (button: HTMLButtonElement) => void;
  constructor (element: HTMLDivElement, data: any, options: Map<string, string>) {
    this.element = element;
    this.data = data;
    this.options = options;
    this.base_url = options.get('base_url') || PageConfig.getBaseUrl();
    this.style();
    this.make_row();

  }
};

Notebook.prototype.style = function () {
  this.element.classList.add('list_item')
  this.element.classList.add("row");
};

Notebook.prototype.make_button = function () {
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
      that.validate(reply, button);


      console.log(reply);
    } catch (reason) {
      remove_children(container);
      container.innerText = 'Error validating assignment.';
      console.error(
        `Error on POST /assignment_list/assignments/validate ${dataToSend}.\n${reason}`
      );
    }
    
  }

  return container;
};

Notebook.prototype.validate_success = function (button: HTMLButtonElement) {
  button.classList.remove('btn-default', 'btn-danger', 'btn-success');
  button.classList.add('btn-success');
};

Notebook.prototype.validate_failure = function (button: HTMLButtonElement) {
  button.classList.remove('btn-default', 'btn-danger', 'btn-success');
  button.classList.add("btn-danger");
};

Notebook.prototype.validate = function (data, button) {
  var body = document.createElement('div') as HTMLDivElement;
  body.setAttribute('id', 'validation-message')
  if (data['success']) {
      if (typeof(data.value) === "string") {
          data = JSON.parse(data.value);
      } else {
          data = data.value;
      }
      if (data['changed'] !== undefined) {
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
        this.validate_failure(button);

      } else if (data['passed'] !== undefined) {
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
        this.validate_failure(button);

      } else if (data['failed'] !== undefined) {
        for (var i=0; i<data.failed.length; i++) {
          var div = document.createElement('div');
          var paragraph = document.createElement('p');
          paragraph.innerText = 'The following cell failed:';
          var pre = document.createElement('pre');
          pre.innerText = data.failed[i].source;
          pre.innerHTML = data.failed[i].error;
        }
        body.classList.add("validation-failed");
        this.validate_failure(button);

      } else {
        var div = document.createElement('div')
        var paragraph  = document.createElement('p')
        paragraph.innerText = 'Success! Your notebook passes all the tests.';
        div.append(paragraph);
        body.append(div);

        body.classList.add("validation-success");
        this.validate_success(button);
      }

  } else {
    var div  = document.createElement('div');
    var paragraph = document.createElement('p');
    paragraph.innerText = 'There was an error running the validate command:';
    div.append(paragraph);
    body.append(div);
    var pre = document.createElement('pre');
    pre.innerText = data.value
    body.append(pre);

    this.validate_failure(button);
  }


  showDialog({
    title: "Validation Results",
    body: body.innerText,
    buttons: [Dialog.okButton()]
  });


};

Notebook.prototype.make_row = function () {
  var container = document.createElement('div');
  container.classList.add('col-md-12');
  var url = URLExt.join(this.base_url, 'tree', encodeURI(this.data['path']));
  var s1 = document.createElement('span');
  s1.classList.add('item_name', 'col-sm-6');

  var a = document.createElement('a');
  a.setAttribute("href", url);
  a.setAttribute("target", "_blank");
  a.innerText = this.data['notebook_id']
  s1.append(a);

  container.append(s1);
  var s2 = document.createElement('span');
  s2.classList.add('item_course', 'col-sm-2');
  container.append(s2);
  container.append(this.make_button());
  this.element.append(container);
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
  load_list: () => void;
  bind_events: () => void;
  handle_load_list: (data: any) => void;
  load_list_success: (data: any) => void;
  enable_list: () => void;
  disable_list: () => void;
  clear_list: () => void;
  change_course: (course: any) => void;
  load_assignment_list_success: () => void;

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
  this.refresh_element.onclick = function(){
    that.load_list();
  }
  this.bind_events()
  var that = this;

  // to mimick the dropdown of classes
  this.dropdown_element.onclick = function (){
    var d = widget.node.getElementsByTagName('div').namedItem('course_drop_down');
    if(d.classList.contains('open')){
      d.classList.remove('open')
    }else{
      d.classList.add('open');
    } 
  }

}
}

CourseList.prototype.enable_list = function () {
  this.dropdown_element.removeAttribute("disabled");
};

CourseList.prototype.disable_list = function () {
  this.dropdown_element.setAttribute("disabled", "disabled");
};

CourseList.prototype.clear_list = function () {
  // remove list items
  if(this.course_list_element.children.length > 0){
    this.course_list_element.innerHTML = '';

  }

};

CourseList.prototype.bind_events = function () {
  this.refresh_element.click();
};

CourseList.prototype.load_list = async function () {
  this.disable_list()
  this.clear_list();
  this.assignment_list.clear_list(true);

  try {
    const data = await requestAPI<any>('courses');
    console.log(data);
    this.handle_load_list(data)
  } catch (reason) {
    console.error(`Error on GET /assignment_list/courses.\n${reason}`);
  }

};

CourseList.prototype.handle_load_list = function (data) {
  if (data.success) {
      this.load_list_success(data.value);
  } else {
      this.default_course_element.innerText = "Error fetching courses!";
      this.enable_list();
      this.assignment_list.show_error(data.value);
  }
};

CourseList.prototype.load_list_success = function (data) {
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

CourseList.prototype.change_course = function (course) {
  this.disable_list();
  if (this.current_course !== undefined) {
      this.default_course_element.innerText = course;
  }
  this.current_course = course;
  this.default_course_element.innerText = this.current_course;
  var success = ()=>{this.load_assignment_list_success()}; 
  this.assignment_list.load_list(course, success);
};

CourseList.prototype.load_assignment_list_success = function () {
  if (this.data) {
      var that = this;
      var set_course = function (course: string) {
          return function () { that.change_course(course); };
      }

      for (var i=0; i<this.data.length; i++) {
        var a = document.createElement('a');
        a.setAttribute('href', '#');
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
    'assignment_list', // API Namespace
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error);
  }

  const data = await response.json();

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message);
  }

  return data;
}
