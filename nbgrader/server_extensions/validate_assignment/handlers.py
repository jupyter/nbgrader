"""Tornado handlers for nbgrader assignment list web service."""

import os
import json
import traceback

from tornado import web
from textwrap import dedent

from jupyter_server.utils import url_path_join as ujoin
from jupyter_server.base.handlers import JupyterHandler
from traitlets.config import Config
from jupyter_core.paths import jupyter_config_path

from ...apps import NbGrader
from ...validator import Validator
from ...nbgraderformat import SchemaTooOldError, SchemaTooNewError
from ... import __version__ as nbgrader_version


static = os.path.join(os.path.dirname(__file__), 'static')


class ValidateAssignmentHandler(JupyterHandler):

    @property
    def root_dir(self):
        return self.settings['root_dir']

    def load_config(self):
        paths = jupyter_config_path()
        paths.insert(0, os.getcwd())

        app = NbGrader()
        app.config_file_paths.append(paths)
        app.load_config_file()

        return app.config

    def validate_notebook(self, path):
        fullpath = os.path.join(self.root_dir, path)

        try:
            config = self.load_config()
            validator = Validator(config=config)
            result = validator.validate(fullpath)

        except SchemaTooOldError:
            self.log.error(traceback.format_exc())
            msg = (
                "The notebook '{}' uses an old version "
                "of the nbgrader metadata format. Please **back up this "
                "notebook** and then update the metadata using:\n\nnbgrader update {}\n"
            ).format(fullpath, fullpath)
            self.log.error(msg)
            retvalue = {
                "success": False,
                "value": msg
            }

        except SchemaTooNewError:
            self.log.error(traceback.format_exc())
            msg = (
                "The notebook '{}' uses a newer version "
                "of the nbgrader metadata format. Please update your version of "
                "nbgrader to the latest version to be able to use this notebook."
            ).format(fullpath)
            self.log.error(msg)
            retvalue = {
                "success": False,
                "value": msg
            }

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
        try:
            data = {
                'path' : self.get_argument('path')
            }
        except web.MissingArgumentError:
            data = self.get_json_body()
        output = self.validate_notebook(data['path'])
        self.finish(json.dumps(output))


class NbGraderVersionHandler(JupyterHandler):

    @web.authenticated
    def get(self):
        ui_version = self.get_argument('version')
        if ui_version != nbgrader_version:
            msg = dedent(
                """
                The version of the Validate labextension does not match
                the server extension; the labextension version is {} while the
                server version is {}. This can happen if you have recently
                upgraded nbgrader, and may cause this extension to not work
                correctly. To fix the problem, please see the nbgrader
                installation instructions:
                http://nbgrader.readthedocs.io/en/main/user_guide/installation.html
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
    (r"/assignments/validate", ValidateAssignmentHandler),
    (r"/nbgrader_version", NbGraderVersionHandler)
]


def load_jupyter_server_extension(nbapp):
    """Load the nbserver"""
    nbapp.log.info("Loading the validate_assignment nbgrader serverextension")
    webapp = nbapp.web_app
    base_url = webapp.settings['base_url']

    # compatibility between notebook.notebookapp.NotebookApp and jupyter_server.serverapp.ServerApp
    if nbapp.name == 'jupyter-notebook':
        webapp.settings['root_dir'] = nbapp.notebook_dir
    else:
        webapp.settings['root_dir'] = nbapp.root_dir

    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in default_handlers
    ])
