#!/usr/bin/env python
# encoding: utf-8

import logging

from IPython.utils.traitlets import Unicode, List, Bool, Dict
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.config.application import catch_config_error
from IPython.nbconvert.writers import FilesWriter
from IPython.nbconvert.nbconvertapp import NbConvertApp

nbgrader_aliases = {
    'log-level' : 'Application.log_level',
    'config' : 'BaseIPythonApplication.extra_config_file'
}

nbgrader_flags = {
    'debug': (
        {'Application' : {'log_level' : logging.DEBUG}},
        "set log level to logging.DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : logging.CRITICAL}},
        "set log level to logging.CRITICAL (minimize logging output)"
    ),
}

nbconvert_aliases = {}
nbconvert_aliases.update(nbgrader_aliases)
nbconvert_aliases.update({
    'build-dir': 'FilesWriter.build_directory',
    'files': 'FilesWriter.files',
    'relpath': 'FilesWriter.relpath',
    'output': 'NbConvertApp.output_base',
})

nbconvert_flags = {}
nbconvert_flags.update(nbgrader_flags)
nbconvert_flags.update({
})

class BaseNbGraderApp(BaseIPythonApplication):

    aliases = Dict(nbgrader_aliases)
    flags = Dict(nbgrader_flags)

    profile = Unicode('nbgrader', config=True, help="Default IPython profile to use")
    auto_create = Bool(True, config=True, help="Whether to automatically generate the profile")

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        return [ProfileDir]

    def build_extra_config(self):
        pass

    @catch_config_error
    def initialize(self, argv=None):
        super(BaseNbGraderApp, self).initialize(argv)
        self.stage_default_config_file()
        self.build_extra_config()


class BaseNbConvertApp(BaseNbGraderApp, NbConvertApp):

    aliases = Dict(nbconvert_aliases)
    flags = Dict(nbconvert_flags)

    def _classes_default(self):
        classes = super(BaseNbConvertApp, self)._classes_default()
        classes.append(FilesWriter)
        return classes

    def _export_format_default(self):
        return 'assignment'
