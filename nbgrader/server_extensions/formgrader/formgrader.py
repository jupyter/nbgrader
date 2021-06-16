# coding: utf-8

import os

from nbconvert.exporters import HTMLExporter
from traitlets import default
from tornado import web
from jinja2 import Environment, FileSystemLoader
from notebook.utils import url_path_join as ujoin

from . import handlers, apihandlers
from ...apps.baseapp import NbGrader


class FormgradeExtension(NbGrader):

    name = u'formgrade'
    description = u'Grade a notebook using an HTML form'

    @default("classes")
    def _classes_default(self):
        classes = super(FormgradeExtension, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def build_extra_config(self):
        extra_config = super(FormgradeExtension, self).build_extra_config()
        extra_config.HTMLExporter.template_name = 'formgrade'
        extra_config.HTMLExporter.template_file = 'formgrade.html.j2'
        extra_config.HTMLExporter.extra_template_basedirs.append(handlers.template_path)
        return extra_config

    def init_tornado_settings(self, webapp):
        # Init jinja environment
        jinja_env = Environment(loader=FileSystemLoader([
            os.path.join(handlers.template_path, 'formgrade'),
            os.path.join(handlers.template_path, 'pages')
        ]))

        course_dir = self.coursedir.root
        notebook_dir = self.parent.notebook_dir
        relpath = os.path.relpath(course_dir, notebook_dir)
        if relpath.startswith("../"):
            nbgrader_bad_setup = True
            self.log.error(
                "The course directory root is not a subdirectory of the notebook "
                "server root. This means that nbgrader will not work correctly. "
                "If you want to use nbgrader, please ensure the course directory "
                "root is in a subdirectory of the notebook root: %s", notebook_dir)
        else:
            nbgrader_bad_setup = False

        # Configure the formgrader settings
        tornado_settings = dict(
            nbgrader_url_prefix=os.path.relpath(self.coursedir.root, self.parent.notebook_dir),
            nbgrader_coursedir=self.coursedir,
            nbgrader_authenticator=self.authenticator,
            nbgrader_exporter=HTMLExporter(config=self.config),
            nbgrader_gradebook=None,
            nbgrader_db_url=self.coursedir.db_url,
            nbgrader_jinja2_env=jinja_env,
            nbgrader_bad_setup=nbgrader_bad_setup
        )

        webapp.settings.update(tornado_settings)

    def init_handlers(self, webapp):
        h = []
        h.extend(handlers.default_handlers)
        h.extend(apihandlers.default_handlers)
        h.extend([
            (r"/formgrader/static/(.*)", web.StaticFileHandler, {'path': handlers.static_path}),
            (r"/formgrader/.*", handlers.Template404)
        ])

        def rewrite(x):
            pat = ujoin(webapp.settings['base_url'], x[0].lstrip('/'))
            return (pat,) + x[1:]

        webapp.add_handlers(".*$", [rewrite(x) for x in h])

    def start(self):
        raise NotImplementedError


def load_jupyter_server_extension(nbapp):
    """Load the formgrader extension"""
    nbapp.log.info("Loading the formgrader nbgrader serverextension")
    webapp = nbapp.web_app
    formgrader = FormgradeExtension(parent=nbapp)
    formgrader.log = nbapp.log
    formgrader.initialize([])
    formgrader.init_tornado_settings(webapp)
    formgrader.init_handlers(webapp)

