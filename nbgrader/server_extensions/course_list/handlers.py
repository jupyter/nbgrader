"""Tornado handlers for nbgrader course list web service."""

import os
import contextlib
import json
import traceback

from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPClientError
from tornado import gen
from textwrap import dedent
from six.moves import urllib

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets.config import Config
from jupyter_core.paths import jupyter_config_path

from ...apps import NbGrader
from ...auth import Authenticator
from ...auth.jupyterhub import (JupyterhubEnvironmentError, get_jupyterhub_api_url,
    get_jupyterhub_authorization, get_jupyterhub_url, get_jupyterhub_user)
from ...coursedir import CourseDirectory
from ... import __version__ as nbgrader_version


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(currdir)


class CourseListHandler(IPythonHandler):

    @property
    def assignment_dir(self):
        return self.settings['assignment_dir']

    def get_base_url(self):
        parts = list(urllib.parse.urlsplit(self.request.full_url()))
        base_url = parts[0] + "://" + parts[1]
        return base_url.rstrip("/")

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

    @gen.coroutine
    def check_for_local_formgrader(self, config):
        base_url = self.get_base_url() + "/" + self.base_url.lstrip("/")
        base_url = base_url.rstrip("/")
        url = base_url + "/formgrader/api/status"
        header = {"Authorization": "token {}".format(self.token)}
        http_client = AsyncHTTPClient()
        try:
            response = yield http_client.fetch(url, headers=header)
        except HTTPClientError:
            # local formgrader isn't running
            self.log.warning("Local formgrader does not seem to be running")
            raise gen.Return([])

        try:
            response = json.loads(response.body.decode())
            status = response['status']
        except:
            self.log.error("Couldn't decode response from local formgrader")
            self.log.error(traceback.format_exc())
            raise gen.Return([])

        if status:
            raise gen.Return([{
                'course_id': config.CourseDirectory.course_id,
                'url': base_url + '/formgrader',
                'kind': 'local'
            }])

        self.log.error("Local formgrader not accessible")
        raise gen.Return([])

    @gen.coroutine
    def check_for_noauth_jupyterhub_formgraders(self, config):
        try:
            get_jupyterhub_user()
        except JupyterhubEnvironmentError:
            # Not running on JupyterHub.
            raise gen.Return([])

        # We are running on JupyterHub, so maybe there's a formgrader
        # service. Check if we have a course id and if so guess the path to the
        # formgrader.
        coursedir = CourseDirectory(config=config)
        if not coursedir.course_id:
            raise gen.Return([])

        url = self.get_base_url() + "/services/" + coursedir.course_id + "/formgrader"
        auth = get_jupyterhub_authorization()
        http_client = AsyncHTTPClient()
        try:
            yield http_client.fetch(url, headers=auth)
        except:
            self.log.error("Formgrader not available at URL: %s", url)
            raise gen.Return([])

        courses = [{
            'course_id': coursedir.course_id,
            'url': url,
            'kind': 'jupyterhub'
        }]
        raise gen.Return(courses)

    @gen.coroutine
    def check_for_jupyterhub_formgraders(self, config):
        # first get the list of courses from the authenticator
        auth = Authenticator(config=config)
        try:
            course_names = auth.get_student_courses("*")
        except JupyterhubEnvironmentError:
            # not running on JupyterHub, or otherwise don't have access
            raise gen.Return([])

        # If course_names is None, that means either we're not running with
        # JupyterHub, or we just have a single class for all students and
        # instructors.
        if course_names is None:
            courses = yield self.check_for_noauth_jupyterhub_formgraders(config)
            raise gen.Return(courses)

        base_url = get_jupyterhub_api_url()
        url = base_url + "/services"
        auth = get_jupyterhub_authorization()

        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(url, headers=auth)

        try:
            services = json.loads(response.body.decode())
        except:
            self.log.error("Failed to decode response: %s", response.body)
            raise gen.Return([])

        courses = []
        for course in course_names:
            if course not in services:
                self.log.warning("Couldn't find formgrader for course '%s'", course)
                continue
            service = services[course]
            courses.append({
                'course_id': course,
                'url': self.get_base_url() + service['prefix'].rstrip('/') + "/formgrader",
                'kind': 'jupyterhub'
            })

        raise gen.Return(courses)

    @gen.coroutine
    @web.authenticated
    def get(self):
        with chdir(self.assignment_dir):
            try:
                config = self.load_config()
                courses = []
                local_courses = yield self.check_for_local_formgrader(config)
                jhub_courses = yield self.check_for_jupyterhub_formgraders(config)
                courses.extend(local_courses)
                courses.extend(jhub_courses)

            except:
                self.log.error(traceback.format_exc())
                retvalue = {
                    "success": False,
                    "value": traceback.format_exc()
                }

            else:
                retvalue = {
                    "success": True,
                    "value": sorted(courses, key=lambda x: x['course_id'])
                }

        raise gen.Return(self.finish(json.dumps(retvalue)))


class NbGraderVersionHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        ui_version = self.get_argument('version')
        if ui_version != nbgrader_version:
            msg = dedent(
                """
                The version of the Course List nbextension does not match
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


default_handlers = [
    (r"/formgraders", CourseListHandler),
    (r"/nbgrader_version", NbGraderVersionHandler)
]


def load_jupyter_server_extension(nbapp):
    """Load the nbserver"""
    nbapp.log.info("Loading the course_list nbgrader serverextension")
    webapp = nbapp.web_app
    base_url = webapp.settings['base_url']
    webapp.settings['assignment_dir'] = nbapp.notebook_dir
    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in default_handlers
    ])
