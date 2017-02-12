"""Tornado handlers for nbgrader assignment list web service."""

import os
import json
import subprocess as sp
import sys
import contextlib
import traceback

from tornado import web

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets import Unicode, default
from traitlets.config import LoggingConfigurable, Config
from jupyter_core.paths import jupyter_config_path

from ...apps import NbGrader
from ...coursedir import CourseDirectory
from ...exchange import ExchangeList, ExchangeFetch, ExchangeSubmit


static = os.path.join(os.path.dirname(__file__), 'static')

def load_config():
    paths = jupyter_config_path()
    paths.insert(0, os.getcwd())

    full_config = Config()
    for config in NbGrader._load_config_files("nbgrader_config", path=paths):
        full_config.merge(config)

    return full_config


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(currdir)


class AssignmentList(LoggingConfigurable):

    assignment_dir = Unicode('', help='Directory where the nbgrader commands should be run, relative to NotebookApp.notebook_dir').tag(config=True)

    @default("assignment_dir")
    def _assignment_dir_default(self):
        return self.parent.notebook_dir

    def list_released_assignments(self, course_id=None):
        with chdir(self.assignment_dir):
            try:
                config = load_config()
                if course_id:
                    config.Exchange.course_id = course_id

                coursedir = CourseDirectory(config=config)
                lister = ExchangeList(coursedir=coursedir, config=config)
                assignments = lister.start()

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                for assignment in assignments:
                    if assignment['status'] == 'fetched':
                        assignment['path'] = os.path.relpath(assignment['path'], self.assignment_dir)
                        for notebook in assignment['notebooks']:
                            notebook['path'] = os.path.relpath(notebook['path'], self.assignment_dir)
                retvalue = {
                    "success": True,
                    "value": sorted(assignments, key=lambda x: (x['course_id'], x['assignment_id']))
                }

        return retvalue

    def list_submitted_assignments(self, course_id=None):
        with chdir(self.assignment_dir):
            try:
                config = load_config()
                config.ExchangeList.cached = True
                if course_id:
                    config.Exchange.course_id = course_id

                coursedir = CourseDirectory(config=config)
                lister = ExchangeList(coursedir=coursedir, config=config)
                assignments = lister.start()

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                retvalue = {
                    "success": True,
                    "value": sorted(assignments, key=lambda x: x['timestamp'], reverse=True)
                }

        return retvalue

    def list_assignments(self, course_id=None):
        released = self.list_released_assignments(course_id=course_id)
        if not released['success']:
            return released

        submitted = self.list_submitted_assignments(course_id=course_id)
        if not submitted['success']:
            return submitted

        retvalue = {
            "success": True,
            "value": released["value"] + submitted["value"]
        }

        return retvalue

    def list_courses(self):
        assignments = self.list_assignments()
        if not assignments["success"]:
            return assignments

        retvalue = {
            "success": True,
            "value": sorted(list(set([x["course_id"] for x in assignments["value"]])))
        }

        return retvalue

    def fetch_assignment(self, course_id, assignment_id):
        with chdir(self.assignment_dir):
            try:
                config = load_config()
                config.Exchange.course_id = course_id
                config.CourseDirectory.assignment_id = assignment_id

                coursedir = CourseDirectory(config=config)
                fetch = ExchangeFetch(coursedir=coursedir, config=config)
                fetch.start()

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                retvalue = {
                    "success": True
                }

        return retvalue

    def submit_assignment(self, course_id, assignment_id):
        with chdir(self.assignment_dir):
            try:
                config = load_config()
                config.Exchange.course_id = course_id
                config.CourseDirectory.assignment_id = assignment_id

                coursedir = CourseDirectory(config=config)
                submit = ExchangeSubmit(coursedir=coursedir, config=config)
                submit.start()

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                retvalue = {
                    "success": True
                }

        return retvalue

    def validate_notebook(self, path):
        cmd = [sys.executable, "-m", "nbgrader", "validate", "--json", path]
        p = sp.Popen(
            cmd, stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.assignment_dir)
        stdout, stderr = p.communicate()
        retcode = p.poll()

        if retcode != 0:
            retvalue = {
                "success": False,
                "value": stdout.decode() + stderr.decode(),
                "command": " ".join(cmd)
            }

        else:
            retvalue = {
                "success": True,
                "value": stdout.decode()
            }

        return retvalue


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
            output = self.manager.submit_assignment(course_id, assignment_id)
            if output['success']:
                self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
            else:
                self.finish(json.dumps(output))
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
