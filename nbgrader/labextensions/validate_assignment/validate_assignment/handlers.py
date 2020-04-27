import json

from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
import tornado
from textwrap import dedent

nbgrader_version = '0.7.0.dev'  # TODO: hardcoded value

class NbGraderVersionHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        ui_version = self.get_argument('version')
        if ui_version != nbgrader_version:
            msg = dedent(
                """
                The version of the Validate nbextension does not match
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

class RouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /validate_assignment/get_example endpoint!"
        }))


def setup_handlers(web_app):
    host_pattern = ".*$"
    
    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "validate_assignment", "get_example")
    handlers = [
        # (route_pattern, RouteHandler),
        (url_path_join(base_url, "validate_assignment", "nbgrader_version"),
         NbGraderVersionHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)
