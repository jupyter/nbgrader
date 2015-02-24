from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Integer, List

from IPython.core.application import BaseIPythonApplication
from IPython.core.application import base_aliases, base_flags
from IPython.core.profiledir import ProfileDir
from IPython.nbconvert.exporters import HTMLExporter
from IPython.config.application import catch_config_error

from nbgrader.html.formgrade import app
from nbgrader.api import Gradebook

import os
import logging
import subprocess as sp
import socket
import pipes

aliases = {}
aliases.update(base_aliases)
aliases.update({
    'ip': 'FormgradeApp.ip',
    'port': 'FormgradeApp.port'
})

flags = {}
flags.update(base_flags)

examples = """
nbgrader formgrade .
nbgrader formgrade autograded/
nbgrader formgrade --ip=0.0.0.0 --port=80
"""

def random_port():
    """get a single random port"""
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

class FormgradeApp(BaseIPythonApplication):

    name = Unicode(u'nbgrader-formgrade')
    description = Unicode(u'Grade a notebook using an HTML form')
    aliases = aliases
    flags = flags
    examples = examples

    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to database")
    ip = Unicode("localhost", config=True, help="IP address for the server")
    port = Integer(5000, config=True, help="Port for the server")
    base_directory = Unicode('.', config=True, help="Root server directory")
    directory_format = Unicode('{notebook_id}.ipynb', config=True, help="Format string for the directory structure of the autograded notebooks")

    def _ipython_dir_default(self):
        d = os.path.join(os.environ["HOME"], ".nbgrader")
        self._ipython_dir_changed('ipython_dir', d, d)
        return d

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [
            HTMLExporter,
            ProfileDir
        ]

    def _log_level_default(self):
        return logging.INFO

    def init_server_root(self):
        # Specifying notebooks on the command-line overrides (rather than adds)
        # the notebook list
        if self.extra_args:
            patterns = self.extra_args
        else:
            patterns = [self.base_directory]

        if len(patterns) == 0:
            self.base_directory = '.'

        elif len(patterns) == 1:
            self.base_directory = patterns[0]

        else:
            raise ValueError("Multiple files not supported")

        self.base_directory = os.path.abspath(self.base_directory)

        if not os.path.isdir(self.base_directory):
            raise ValueError("Path is not a directory: {}".format(self.base_directory))

        self.log.info("Server root is: {}".format(self.base_directory))

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.template_file = 'formgrade'
        self.extra_config.Exporter.template_path = [os.path.join(app.root_path, app.template_folder)]
        self.config.merge(self.extra_config)

    @catch_config_error
    def initialize(self, argv=None):
        super(FormgradeApp, self).initialize(argv)
        self.stage_default_config_file()
        self.build_extra_config()
        self.init_server_root()

    def start(self):
        super(FormgradeApp, self).start()

        # first launch a notebook server
        app.notebook_server_ip = self.ip
        app.notebook_server_port = str(random_port())
        app.notebook_server = sp.Popen(
            [
                "python", os.path.join(os.path.dirname(__file__), "notebookapp.py"),
                "--ip", app.notebook_server_ip,
                "--port", app.notebook_server_port
            ],
            cwd=self.base_directory)

        # now launch the formgrader
        app.notebook_dir = self.base_directory
        app.notebook_dir_format = self.directory_format
        app.exporter = HTMLExporter(config=self.config)

        url = "http://{:s}:{:d}/".format(self.ip, self.port)
        self.log.info("Form grader running at {}".format(url))
        self.log.info("Use Control-C to stop this server")

        app.gradebook = Gradebook(self.db_url)
        app.run(host=self.ip, port=self.port, debug=True, use_reloader=False)
