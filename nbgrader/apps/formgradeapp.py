import os
import signal
import sys
import notebook

from nbconvert.exporters import HTMLExporter
from textwrap import dedent
from traitlets import Unicode, Integer, Type, Instance
from traitlets.config.application import catch_config_error

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..formgrader import app
from ..api import Gradebook
from ..auth import BaseAuth, NoAuth

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


class FormgradeApp(NbGrader):

    name = u'nbgrader-formgrade'
    description = u'Grade a notebook using an HTML form'

    aliases = aliases
    flags = flags

    examples = """
        Run the formgrader server application in order to manually grade
        submissions that have already been autograded. Running the formgrader
        allows *any* submission (from any assignment, for any student) to be
        graded, as long as it has already been run through the autograder.

        By default, the formgrader runs at http://localhost:5000. It also starts
        a Jupyter notebook server, to allow students' notebooks to be open up
        and run manually if so desired. The notebook server also runs on
        localhost on a random port, though this port can be specified by setting
        `FormgradeApp.nbserver_port`. The notebook server can be disabled entirely
        by setting `FormgradeApp.start_nbserver=False`.

        The formgrader must be run from the root of a nbgrader-compatible directory
        structure, which by default looks like:

            autograded/{student_id}/{assignment_id}/{notebook_id}.ipynb

        To run the formgrader on the default IP and port:
            nbgrader formgrade

        To run the formgrader on a public-facing IP address:
            nbgrader formgrade --ip 0.0.0.0

        To run the formgrader a different port:
            nbgrader formgrade --port 5001
        """

    ip = Unicode("localhost", config=True, help="IP address for the server")
    port = Integer(5000, config=True, help="Port for the server")
    authenticator_class = Type(NoAuth, klass=BaseAuth, config=True, help="""
        Authenticator used in all formgrade requests.""")
    authenticator_instance = Instance(BaseAuth, config=False)

    base_directory = Unicode(os.path.abspath('.'))

    mathjax_url = Unicode(
        '',
        config=True,
        help=dedent(
            """
            URL or local path to mathjax installation. Defaults to the version
            of MathJax included with the Jupyter Notebook.
            """
        )
    )

    def _mathjax_url_default(self):
        url = os.path.join(notebook.DEFAULT_STATIC_FILES_PATH, 'components', 'MathJax', 'MathJax.js')
        if not os.path.exists(url):
            url = 'https://cdn.mathjax.org/mathjax/latest/MathJax.js'
        self.log.info("Serving MathJax from %s", url)
        return url

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
        sys.exit(0)

    def build_extra_config(self):
        extra_config = super(FormgradeApp, self).build_extra_config()
        extra_config.Exporter.template_file = 'formgrade'
        extra_config.Exporter.template_path = [os.path.join(app.root_path, app.template_folder)]
        return extra_config

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
        app.nbgrader_step = self.autograded_directory
        app.exporter = HTMLExporter(config=self.config)
        app.mathjax_url = self.mathjax_url

        url = "http://{:s}:{:d}/".format(self.ip, self.port)
        self.log.info("Form grader running at {}".format(url))
        self.log.info("Use Control-C to stop this server")

        app.gradebook = Gradebook(self.db_url)
        app.run(host=self.ip, port=self.port, debug=True, use_reloader=False)
