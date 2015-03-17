import os
import signal
import sys

from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Integer, Dict, Type, \
    Instance

from IPython.nbconvert.exporters import HTMLExporter
from IPython.config.application import catch_config_error

from nbgrader.apps.baseapp import BaseNbGraderApp, nbgrader_aliases, nbgrader_flags
from nbgrader.html.formgrade import app
from nbgrader.api import Gradebook
from nbgrader.auth import BaseAuth, NoAuth

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    'ip': 'FormgradeApp.ip',
    'port': 'FormgradeApp.port',
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
})


class FormgradeApp(BaseNbGraderApp):

    name = Unicode(u'nbgrader-formgrade')
    description = Unicode(u'Grade a notebook using an HTML form')
    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        nbgrader formgrade .
        nbgrader formgrade autograded/
        nbgrader formgrade --ip=0.0.0.0 --port=80
        """
    ))

    nbgrader_step_input = Unicode("autograded")
    nbgrader_step_output = Unicode("")

    ip = Unicode("localhost", config=True, help="IP address for the server")
    port = Integer(5000, config=True, help="Port for the server")
    authenticator_class = Type(NoAuth, klass=BaseAuth, config=True, help="""
        Authenticator used in all formgrade requests.""")
    authenticator_instance = Instance(BaseAuth, config=False)

    base_directory = Unicode(os.path.abspath('.'))

    def _classes_default(self):
        classes = super(FormgradeApp, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def init_signal(self):
        signal.signal(signal.SIGINT, self._signal_stop)
        signal.signal(signal.SIGTERM, self._signal_stop)

    def _signal_stop(self, sig, frame):
        self.log.critical("received signal %s, stopping", sig)
        self.authenticator_instance.stop(sig)
        sys.exit(-sig)

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.template_file = 'formgrade'
        self.extra_config.Exporter.template_path = [os.path.join(app.root_path, app.template_folder)]
        self.config.merge(self.extra_config)

    @catch_config_error
    def initialize(self, argv=None):
        super(FormgradeApp, self).initialize(argv)
        self.init_signal()

    def start(self):
        super(FormgradeApp, self).start()

        # Init authenticator.
        self.authenticator_instance = self.authenticator_class(
            app,
            self.ip,
            self.port,
            self.base_directory,
            parent=self)
        app.auth = self.authenticator_instance

        # now launch the formgrader
        app.notebook_dir = self.base_directory
        app.notebook_dir_format = self.directory_structure
        app.nbgrader_step = self.nbgrader_step_input
        app.exporter = HTMLExporter(config=self.config)

        url = "http://{:s}:{:d}/".format(self.ip, self.port)
        self.log.info("Form grader running at {}".format(url))
        self.log.info("Use Control-C to stop this server")

        app.gradebook = Gradebook(self.db_url)
        app.run(host=self.ip, port=self.port, debug=True, use_reloader=False)
