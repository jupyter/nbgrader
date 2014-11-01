from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Integer, List

from IPython.core.application import BaseIPythonApplication
from IPython.nbconvert.exporters import HTMLExporter
from IPython.config.application import catch_config_error

from nbgrader.html.formgrade import app
from nbgrader.api import Gradebook

import os
import logging


aliases = {
    'ip': 'FormgradeApp.ip',
    'port': 'FormgradeApp.port'
}

flags = {}

examples = """
nbgrader formgrade .
nbgrader formgrade autograded/
nbgrader formgrade --ip=0.0.0.0 --port=80
"""

class FormgradeApp(BaseIPythonApplication):

    name = Unicode(u'nbgrader-formgrade')
    description = Unicode(u'Grade a notebook using an HTML form')
    aliases = aliases
    flags = flags
    examples = examples
    ipython_dir = "/tmp/nbgrader"

    db_name = Unicode("gradebook", config=True, help="Database name")
    db_ip = Unicode("localhost", config=True, help="IP address for the database")
    db_port = Integer(27017, config=True, help="Port for the database")

    ip = Unicode("localhost", config=True, help="IP address for the server")
    port = Integer(5000, config=True, help="Port for the server")
    base_directory = Unicode('.', config=True, help="Root server directory")
    directory_format = Unicode('{notebook_id}.ipynb', config=True, help="Format string for the directory structure of the autograded notebooks")

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [
            HTMLExporter
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

        app.notebook_dir = self.base_directory
        app.notebook_dir_format = self.directory_format
        app.exporter = HTMLExporter(config=self.config)

        url = "http://{:s}:{:d}/".format(self.ip, self.port)
        self.log.info("Form grader running at {}".format(url))
        self.log.info("Use Control-C to stop this server")

        app.gradebook = Gradebook(self.db_name, ip=self.db_ip, port=self.db_port)
        app.run(host=self.ip, port=self.port, debug=True, use_reloader=False)
