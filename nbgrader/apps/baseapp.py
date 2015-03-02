#!/usr/bin/env python
# encoding: utf-8

import logging

from IPython.utils.traitlets import Unicode, List, Bool, Dict
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.config.application import catch_config_error
from IPython.nbconvert.writers import FilesWriter
from IPython.nbconvert.nbconvertapp import NbConvertApp

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseNbGraderApp (and not BaseNbConvertApp)
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

# These are the aliases and flags for nbgrade apps that inherit from BaseNbConvertApp
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
    """A base class for all the nbgrader apps. This sets a few important defaults,
    like the IPython profile (nbgrader) and that this profile should be created
    automatically if it doesn't exist.

    Additionally, it defines a `build_extra_config` method that subclasses can
    override in order to specify extra config options.

    """

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
    """A base class for all the nbgrader apps that utilize nbconvert. This
    inherits defaults from BaseNbGraderApp, while exposing nbconvert's
    functionality of running preprocessors and writing a new file.

    The default export format is 'assignment', which is a special export format
    defined in nbgrader (see nbgrader.exporters.assignmentexporter) that
    includes a few things that nbgrader needs (such as the path to the file).

    """

    aliases = Dict(nbconvert_aliases)
    flags = Dict(nbconvert_flags)

    def _classes_default(self):
        classes = super(BaseNbConvertApp, self)._classes_default()
        classes.append(FilesWriter)
        return classes

    def _export_format_default(self):
        return 'assignment'
