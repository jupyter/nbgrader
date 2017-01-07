# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
ioloop.install()

import os
import signal
import notebook
import logging
import sys

from nbconvert.exporters import HTMLExporter
from textwrap import dedent
from traitlets import Unicode, Integer, Type, Instance, default
from traitlets.config.application import catch_config_error
from tornado import web
from tornado.ioloop import IOLoop
from tornado.log import app_log, access_log, gen_log
from jinja2 import Environment, FileSystemLoader

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..formgrader import handlers, apihandlers
from ..api import Gradebook
from ..auth import BaseAuth, NoAuth, HubAuth

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

    ip = Unicode("localhost", help="IP address for the server").tag(config=True)
    port = Integer(5000, help="Port for the server").tag(config=True)

    authenticator_class = Type(
        NoAuth,
        klass=BaseAuth,
        help="""Authenticator used in all formgrade requests."""
    ).tag(config=True)

    authenticator_instance = Instance(BaseAuth).tag(config=False)

    mathjax_url = Unicode(
        '',
        help=dedent(
            """
            URL or local path to mathjax installation. Defaults to the version
            of MathJax included with the Jupyter Notebook.
            """
        )
    ).tag(config=True)

    @default("mathjax_url")
    def _mathjax_url_default(self):
        url = os.path.join(notebook.DEFAULT_STATIC_FILES_PATH, 'components', 'MathJax', 'MathJax.js')
        if not os.path.exists(url):
            url = 'https://cdn.mathjax.org/mathjax/latest/MathJax.js'
        self.log.info("Serving MathJax from %s", url)
        return url

    @default("classes")
    def _classes_default(self):
        classes = super(FormgradeApp, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def init_signal(self):
        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, self._signal_stop)
        signal.signal(signal.SIGINT, self._signal_stop)
        signal.signal(signal.SIGTERM, self._signal_stop)

    def _signal_stop(self, sig, frame):
        self.log.critical("Received signal %s, stopping", sig)
        self.authenticator_instance.stop()
        ioloop.IOLoop.current().stop()

        # close the gradebook
        self.tornado_settings['nbgrader_gradebook'].close()

    def build_extra_config(self):
        extra_config = super(FormgradeApp, self).build_extra_config()
        extra_config.Exporter.template_file = 'formgrade'
        extra_config.Exporter.template_path = [handlers.template_path]
        return extra_config

    @catch_config_error
    def initialize(self, argv=None):
        super(FormgradeApp, self).initialize(argv)
        self.init_signal()

    def init_logging(self, handler_class=None, handler_args=None, color=True, subapps=False):
        if handler_class:
            super(FormgradeApp, self).init_logging(handler_class, handler_args, color=color, subapps=subapps)

        # hook up tornado 3's loggers to our app handlers
        self.log.propagate = False
        for log in (app_log, access_log, gen_log):
            # ensure all log statements identify the application they come from
            log.name = self.log.name
        logger = logging.getLogger('tornado')
        logger.propagate = True
        logger.parent = self.log
        logger.setLevel(self.log.level)

    def init_tornado_settings(self):
        # Init authenticator.
        self.authenticator_instance = self.authenticator_class(
            self.ip,
            self.port,
            self.course_directory,
            parent=self)

        # Init jinja environment
        jinja_env = Environment(loader=FileSystemLoader([handlers.template_path]))

        # Configure the formgrader settings
        self.tornado_settings = dict(
            nbgrader_auth=self.authenticator_instance,
            nbgrader_notebook_dir=self.course_directory,
            nbgrader_notebook_dir_format=self.directory_structure,
            nbgrader_step=self.autograded_directory,
            nbgrader_exporter=HTMLExporter(config=self.config),
            nbgrader_mathjax_url=self.mathjax_url,
            nbgrader_gradebook=Gradebook(self.db_url),
            nbgrader_jinja2_env=jinja_env,
            nbgrader_log=self.log,
            login_url=self.authenticator_instance.login_url
        )

    def init_handlers(self):
        h = []
        h.extend(handlers.default_handlers)
        h.extend(apihandlers.default_handlers)
        h.extend([
            (r"/mathjax/(.*)", web.StaticFileHandler, {'path': os.path.dirname(self.mathjax_url)}),
            (r"/static/(.*)", web.StaticFileHandler, {'path': handlers.static_path}),
            (r".*", handlers.Template404)
        ])

        self.handlers = [self.authenticator_instance.transform_handler(handler) for handler in h]

    def init_tornado_application(self):
        self.tornado_application = web.Application(self.handlers, **self.tornado_settings)

    def start(self):
        super(FormgradeApp, self).start()

        if self.logfile:
            self.init_logging(logging.FileHandler, [self.logfile], color=False)
        else:
            self.init_logging()

        self.init_tornado_settings()
        self.init_handlers()
        self.init_tornado_application()

        # Create the application
        self.io_loop = ioloop.IOLoop.current()
        try:
            self.tornado_application.listen(self.port, address=self.ip)
        except OSError as err:
            if err.errno == 48:
                self.log.error("Address already in use by another process: http://{}:{}".format(self.ip, self.port))
                self.log.error("Try running nbgrader with a different port, e.g. nbgrader formgrade --port=5001")
                sys.exit(1)
            else:
                raise

        if not isinstance(self.authenticator_instance, HubAuth):
            if self.authenticator_instance.notebook_server_exists():
                url = self.authenticator_instance.get_notebook_url("")
                self.log.info("Notebook server is running at {}".format(url))

            url = "http://{:s}:{:d}/".format(self.ip, self.port)
            self.log.info("The formgrader is running at {}".format(url))
            self.log.info("--> Go to {} to access the formgrader".format(url))
            self.log.info("Use Control-C to stop this server")

        if sys.platform.startswith('win'):
            # add no-op to wake every 1s
            # to handle signals that may be ignored by the inner loop
            pc = ioloop.PeriodicCallback(lambda : None, 1000)
            pc.start()

        # Start the loop
        self.io_loop.start()
