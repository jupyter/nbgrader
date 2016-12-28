"""Tornado handlers for nbgrader assignment list web service."""

import os
import json
import subprocess as sp
import sys

from tornado import web

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets import Unicode
from traitlets.config import LoggingConfigurable

static = os.path.join(os.path.dirname(__file__), 'static')

class AssignmentList(LoggingConfigurable):

    assignment_dir = Unicode('', config=True, help='Directory where the nbgrader commands should be run, relative to NotebookApp.notebook_dir')
    def _assignment_dir_default(self):
        return self.parent.notebook_dir

    def list_released_assignments(self, course_id=None):
        cmd = [sys.executable, "-m", "nbgrader", "list", "--json"]
        if course_id:
            cmd.extend(["--course", course_id])
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.assignment_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader list exited with code {}'.format(retcode))
        assignments = json.loads(output.decode())
        for assignment in assignments:
            if assignment['status'] == 'fetched':
                assignment['path'] = os.path.relpath(assignment['path'], self.assignment_dir)
                for notebook in assignment['notebooks']:
                    notebook['path'] = os.path.relpath(notebook['path'], self.assignment_dir)
        return sorted(assignments, key=lambda x: (x['course_id'], x['assignment_id']))

    def list_submitted_assignments(self, course_id=None):
        cmd = [sys.executable, "-m", "nbgrader", "list", "--json", "--cached"]
        if course_id:
            cmd.extend(["--course", course_id])
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.assignment_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader list exited with code {}'.format(retcode))
        assignments = json.loads(output.decode())
        return sorted(assignments, key=lambda x: x['timestamp'], reverse=True)

    def list_assignments(self, course_id=None):
        assignments = []
        assignments.extend(self.list_released_assignments(course_id=course_id))
        assignments.extend(self.list_submitted_assignments(course_id=course_id))
        return assignments

    def list_courses(self):
        assignments = self.list_assignments()
        courses = sorted(list(set([x["course_id"] for x in assignments])))
        return courses

    def fetch_assignment(self, course_id, assignment_id):
        p = sp.Popen([
            sys.executable, "-m", "nbgrader", "fetch",
            "--course", course_id,
            assignment_id
        ], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self.assignment_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            self.log.error(output)
            raise RuntimeError('nbgrader fetch exited with code {}'.format(retcode))

    def submit_assignment(self, course_id, assignment_id):
        p = sp.Popen([
            sys.executable, "-m", "nbgrader", "submit",
            "--course", course_id,
            assignment_id
        ], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self.assignment_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            self.log.error(output)
            raise RuntimeError('nbgrader submit exited with code {}'.format(retcode))

    def validate_notebook(self, path):
        p = sp.Popen(
            [sys.executable, "-m", "nbgrader", "validate", "--json", path],
            stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.assignment_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader validate exited with code {}'.format(retcode))
        return output.decode()


class BaseAssignmentHandler(IPythonHandler):

    @property
    def manager(self):
        return self.settings['assignment_list_manager']


class AssignmentListHandler(BaseAssignmentHandler):

    @web.authenticated
    def get(self):
        course_id = self.get_argument('course_id')
        self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))


class AssignmentActionHandler(BaseAssignmentHandler):

    @web.authenticated
    def post(self, action):
        if action == 'fetch':
            assignment_id = self.get_argument('assignment_id')
            course_id = self.get_argument('course_id')
            self.manager.fetch_assignment(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
        elif action == 'submit':
            assignment_id = self.get_argument('assignment_id')
            course_id = self.get_argument('course_id')
            self.manager.submit_assignment(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
        elif action == 'validate':
            output = self.manager.validate_notebook(self.get_argument('path'))
            self.finish(json.dumps(output))


class CourseListHandler(BaseAssignmentHandler):

    @web.authenticated
    def get(self):
        self.finish(json.dumps(self.manager.list_courses()))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_assignment_action_regex = r"(?P<action>fetch|submit|validate)"

default_handlers = [
    (r"/assignments", AssignmentListHandler),
    (r"/assignments/%s" % _assignment_action_regex, AssignmentActionHandler),
    (r"/courses", CourseListHandler),
]


def load_jupyter_server_extension(nbapp):
    """Load the nbserver"""
    nbapp.log.info("Loading the assignment_list nbgrader serverextension")
    webapp = nbapp.web_app
    webapp.settings['assignment_list_manager'] = AssignmentList(parent=nbapp)
    base_url = webapp.settings['base_url']
    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in default_handlers
    ])
