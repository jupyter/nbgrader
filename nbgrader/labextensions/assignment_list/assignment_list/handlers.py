import json
import os
import contextlib
import traceback
from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
import tornado
from textwrap import dedent
from traitlets.config import LoggingConfigurable, Config
from jupyter_core.paths import jupyter_config_path
from nbgrader.exchange import ExchangeFactory, ExchangeError
from nbgrader.apps import NbGrader
from nbgrader.coursedir import CourseDirectory
from nbgrader.auth import Authenticator
from nbgrader import __version__ as nbgrader_version


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

        app = NbGrader()
        app.config_file_paths.append(paths)
        app.load_config_file()

        return app.config


    @contextlib.contextmanager
    def get_assignment_dir_config(self):
        # first get the exchange assignment directory
        with chdir(self.parent.notebook_dir):
            config = self.load_config()

        lister = ExchangeFactory(config=config).List(config=config)
        assignment_dir = lister.assignment_dir

        # now cd to the full assignment directory and load the config again
        with chdir(assignment_dir):

            app = NbGrader()
            app.config_file_paths.append(os.getcwd())
            app.load_config_file()

            yield app.config


    def list_released_assignments(self, course_id=None):
        with self.get_assignment_dir_config() as config:
            try:
                if course_id:
                    config.CourseDirectory.course_id = course_id

                coursedir = CourseDirectory(config=config)
                authenticator = Authenticator(config=config)
                lister = ExchangeFactory(config=config).List(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
                assignments = lister.start()

            except Exception as e:
                self.log.error(traceback.format_exc())
                if isinstance(e, ExchangeError):
                    retvalue = {
                        "success": False,
                        "value": """The exchange directory does not exist and could
                                    not be created. The "release" and "collect" functionality will not be available.
                                    Please see the documentation on
                                    http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange
                                    for instructions.
                                """
                    }
                else:
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
                lister = ExchangeFactory(config=config).List(
                    coursedir=coursedir,
                    authenticator=authenticator,
                    config=config)
                assignments = lister.start()

            except Exception as e:
                self.log.error(traceback.format_exc())
                if isinstance(e, ExchangeError):
                    retvalue = {
                        "success": False,
                        "value": """The exchange directory does not exist and could
                                    not be created. The "release" and "collect" functionality will not be available.
                                    Please see the documentation on
                                    http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange
                                    for instructions.
                                """
                    }
                else:
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
                fetch = ExchangeFactory(config=config).FetchAssignment(
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
                fetch = ExchangeFactory(config=config).FetchFeedback(
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
                submit = ExchangeFactory(config=config).Submit(
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


class BaseAssignmentHandler(APIHandler):

    @property
    def manager(self):
        return self.settings['assignment_list']


class RouteHandler(BaseAssignmentHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /assignment_list/get_example endpoint!"
        }))


class CouseListHandler(BaseAssignmentHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps(self.manager.list_courses()))


class AssignmentListHandler(BaseAssignmentHandler):

    @tornado.web.authenticated
    def get(self):
        course_id = self.get_argument('course_id')
        self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))


class AssignmentActionHandler(BaseAssignmentHandler):

    @tornado.web.authenticated
    def post(self, action):
        input_data = self.get_json_body()
        if action == 'fetch':
            assignment_id = input_data['assignment_id']
            course_id = input_data['course_id']
            self.manager.fetch_assignment(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
        elif action == 'submit':
            assignment_id = input_data['assignment_id']
            course_id = input_data['course_id']
            output = self.manager.submit_assignment(course_id, assignment_id)
            if output['success']:
                self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
            else:
                self.finish(json.dumps(output))
        elif action == 'fetch_feedback':
            assignment_id = input_data['assignment_id']
            course_id = input_data['course_id']
            self.manager.fetch_feedback(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_assignments(course_id=course_id)))
        elif action == 'validate':
            self.finish({"success": True, "value": {}})


class NbGraderVersionHandler(BaseAssignmentHandler):
    @tornado.web.authenticated
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


def setup_handlers(lab_app):
    host_pattern = ".*$"
    _assignment_action_regex = r"(?P<action>fetch|submit|validate|fetch_feedback)"
    url = 'assignment_list'
    lab_app.web_app.settings[url] = AssignmentList(parent=lab_app)
    base_url = lab_app.web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, url, "get_example")
    courses_pattern = url_path_join(base_url, url, "courses")
    assignments_pattern = url_path_join(base_url, url, "assignments")
    assignments_action_pattern = url_path_join(base_url, url, (r"/assignments/%s" % _assignment_action_regex))
    check_nbgrader_pattern = url_path_join(base_url, url, "/nbgrader_version")
    handlers = [(route_pattern, RouteHandler), (courses_pattern, CouseListHandler), (assignments_pattern, AssignmentListHandler), (assignments_action_pattern, AssignmentActionHandler), (check_nbgrader_pattern, NbGraderVersionHandler)]
    lab_app.web_app.add_handlers(host_pattern, handlers)
