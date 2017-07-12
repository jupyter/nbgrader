"""Tornado handlers for nbgrader assignment list web service."""

import os
import json
import contextlib
import traceback

from tornado import web

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets.config import Config
from jupyter_core.paths import jupyter_config_path

from ...apps import NbGrader
from ...validator import Validator
from ... import __version__ as nbgrader_version


static = os.path.join(os.path.dirname(__file__), 'static')


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(currdir)


class ValidateAssignmentHandler(IPythonHandler):

    def load_config(self):
        paths = jupyter_config_path()
        paths.insert(0, os.getcwd())

        config_found = False
        full_config = Config()
        for config in NbGrader._load_config_files("nbgrader_config", path=paths, log=self.log):
            full_config.merge(config)
            config_found = True

        if not config_found:
            self.log.warning("No nbgrader_config.py file found. Rerun with DEBUG log level to see where nbgrader is looking.")

        return full_config

    def validate_notebook(self, path):
        try:
            config = self.load_config()
            validator = Validator(config=config)
            result = validator.validate(path)

        except:
            self.log.error(traceback.format_exc())
            retvalue = {
                "success": False,
                "value": traceback.format_exc()
            }

        else:
            retvalue = {
                "success": True,
                "value": result
            }

        return retvalue

    @web.authenticated
    def post(self):
        output = self.validate_notebook(self.get_argument('path'))
        self.finish(json.dumps(output))


class NbGraderVersionHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.finish(nbgrader_version)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

default_handlers = [
    (r"/assignments/validate", ValidateAssignmentHandler),
    (r"/nbgrader_version", NbGraderVersionHandler)
]


def load_jupyter_server_extension(nbapp):
    """Load the nbserver"""
    nbapp.log.info("Loading the validate_assignment nbgrader serverextension")
    webapp = nbapp.web_app
    base_url = webapp.settings['base_url']
    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in default_handlers
    ])
