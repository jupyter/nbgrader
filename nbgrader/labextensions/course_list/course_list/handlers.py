import json

from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
from textwrap import dedent
import tornado

nbgrader_version = '0.7.0.dev'

# TODO: Port over CourseListHandler and understand exactly how formgrader works and why it needs to talk to it

class MockCourseListHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "success": True,
            "value": [
                {
                    'course_id': 'test1',
                    'url': 'https://example.com/',
                    'kind': 'local'
                },
                {
                    'course_id': 'test2',
                    'url': 'https://example.com/',
                    'kind': 'jupyterhub'
                }
            ]
        }))



class NbGraderVersionHandler(APIHandler):
    @tornado.web.authenticated
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


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "course_list", "get_example")
    handlers = [
        (url_path_join(base_url, "course_list", "formgraders"), MockCourseListHandler),
        (url_path_join(base_url, "course_list", "nbgrader_version"), NbGraderVersionHandler)
    ]
    web_app.add_handlers(host_pattern, handlers)
