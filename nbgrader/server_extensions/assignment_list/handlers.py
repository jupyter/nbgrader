"""Tornado handlers for nbgrader assignment list web service."""

import os
import json
import contextlib
import traceback

from tornado import web
from textwrap import dedent

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets import Unicode, default
from traitlets.config import LoggingConfigurable, Config
from jupyter_core.paths import jupyter_config_path

from ...apps import NbGrader
from ...coursedir import CourseDirectory
from ...exchange import ExchangeList, ExchangeFetchAssignment, ExchangeFetchFeedback, ExchangeSubmit
from ...auth import Authenticator
from ... import __version__ as nbgrader_version


static = os.path.join(os.path.dirname(__file__), 'static')


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(currdir)


class AssignmentList(LoggingConfigurable):

    def load_config(self):
        paths = jupyter_config_path()
        paths.insert(0, os.getcwd())

        config_found = False
        full_config = Config()
        for config, filename in NbGrader._load_config_files("nbgrader_config", path=paths, log=self.log):
            full_config.merge(config)
            config_found = True

        if not config_found:
            self.log.warning("No nbgrader_config.py file found. Rerun with DEBUG log level to see where nbgrader is looking.")

        return full_config

    @contextlib.contextmanager
    def get_assignment_dir_config(self):
        # first get the exchange assignment directory
        with chdir(self.parent.notebook_dir):
            config = self.load_config()

        lister = ExchangeList(config=config)
        assignment_dir = lister.assignment_dir

        # now cd to the full assignment directory and load the config again
        with chdir(assignment_dir):
            for new_config, filename in NbGrader._load_config_files("nbgrader_config", path=[os.getcwd()], log=self.log):
                config.merge(new_config)
            yield config

    def list_released_assignments(self, course_id=None):
        with self.get_assignment_dir_config() as config:
            try:
                if course_id:
                    config.CourseDirectory.course_id = course_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                lister = ExchangeList(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
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
                        assignment['path'] = os.path.relpath(assignment['path'], self.parent.notebook_dir)
                        for notebook in assignment['notebooks']:
                            notebook['path'] = os.path.relpath(notebook['path'], self.parent.notebook_dir)
                retvalue = {
                    "success": True,
                    "value": sorted(assignments, key=lambda x: (x['course_id'], x['assignment_id']))
                }

        return retvalue

    def list_submitted_assignments(self, course_id=None):
        with self.get_assignment_dir_config() as config:
            try:
                config.ExchangeList.cached = True
                if course_id:
                    config.CourseDirectory.course_id = course_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                lister = ExchangeList(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
                assignments = lister.start()

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                for assignment in assignments:
                    assignment["submissions"] = sorted(
                        assignment["submissions"],
                        key=lambda x: x["timestamp"])
                assignments = sorted(assignments, key=lambda x: x["assignment_id"])
                retvalue = {
                    "success": True,
                    "value": assignments
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
        with self.get_assignment_dir_config() as config:
            try:
                config = self.load_config()
                config.CourseDirectory.course_id = course_id
                config.CourseDirectory.assignment_id = assignment_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                fetch = ExchangeFetchAssignment(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
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


    def fetch_feedback(self, course_id, assignment_id):
        with self.get_assignment_dir_config() as config:
            try:
                config = self.load_config()
                config.CourseDirectory.course_id = course_id
                config.CourseDirectory.assignment_id = assignment_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                fetch = ExchangeFetchFeedback(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
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
        with self.get_assignment_dir_config() as config:
            try:
                config = self.load_config()
                config.CourseDirectory.course_id = course_id
                config.CourseDirectory.assignment_id = assignment_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                submit = ExchangeSubmit(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
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
        elif action == 'fetch_feedback':
            assignment_id = self.get_argument('assignment_id')
            course_id = self.get_argument('course_id')
            self.manager.fetch_feedback(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))


class CourseListHandler(BaseAssignmentHandler):

    @web.authenticated
    def get(self):
        self.finish(json.dumps(self.manager.list_courses()))


class NbGraderVersionHandler(BaseAssignmentHandler):

    @web.authenticated
    def get(self):
        ui_version = self.get_argument('version')
        if ui_version != nbgrader_version:
            msg = dedent(
                """
                The version of the Assignment List nbextension does not match
                the server extension; the nbextension version is {} while the
                server version is {}. This can happen if you have recently
                upgraded nbgrader, and may cause this extension to not work
                correctly. To fix the problem, please see the nbgrader
                installation instructions:
                http://nbgrader.readthedocs.io/en/stable/user_guide/installation.html
                """.format(ui_version, nbgrader_version)
            ).strip().replace("\n", " ")
            self.log.error(msg)
            result = {"success": False, "message": msg}
        else:
            result = {"success": True}

        self.finish(json.dumps(result))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_assignment_action_regex = r"(?P<action>fetch|submit|fetch_feedback)"

default_handlers = [
    (r"/assignments", AssignmentListHandler),
    (r"/assignments/%s" % _assignment_action_regex, AssignmentActionHandler),
    (r"/courses", CourseListHandler),
    (r"/nbgrader_version", NbGraderVersionHandler)
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
