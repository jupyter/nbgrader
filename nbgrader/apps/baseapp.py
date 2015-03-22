#!/usr/bin/env python
# encoding: utf-8

import logging
import glob
import sys
import re
import os

from IPython.utils.traitlets import Unicode, List, Bool, Dict, Enum
from IPython.core.application import BaseIPythonApplication
from IPython.config.application import catch_config_error
from IPython.nbconvert.nbconvertapp import NbConvertApp, DottedOrNone

from nbgrader.config import BasicConfig, NbGraderConfig

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseApp (and not BaseNbGraderApp)
base_aliases = {
    'log-level' : 'BasicConfig.log_level',
    'config' : 'BasicConfig.extra_config_file',
}
base_flags = {
    'debug': (
        {'BasicConfig' : {'log_level' : logging.DEBUG}},
        "set log level to logging.DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'BasicConfig' : {'log_level' : logging.CRITICAL}},
        "set log level to logging.CRITICAL (minimize logging output)"
    ),
}

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseNbGraderApp (and not BaseNbConvertApp)
nbgrader_aliases = {}
nbgrader_aliases.update(base_aliases)
nbgrader_aliases.update({
    'student': 'NbGraderConfig.student_id',
    'assignment': 'NbGraderConfig.assignment_id',
    'notebook': 'NbGraderConfig.notebook_id',
    'db': 'NbGraderConfig.db_url'
})
nbgrader_flags = {}
nbgrader_flags.update(base_flags)
nbgrader_flags.update({
})

# These are the aliases and flags for nbgrade apps that inherit from BaseNbConvertApp
nbconvert_aliases = {}
nbconvert_aliases.update(nbgrader_aliases)
nbconvert_aliases.update({
})
nbconvert_flags = {}
nbconvert_flags.update(nbgrader_flags)
nbconvert_flags.update({
})

class BaseApp(BaseIPythonApplication):
    """A base class for all the nbgrader apps. This sets a few important defaults,
    like the IPython profile (nbgrader) and that this profile should be created
    automatically if it doesn't exist.

    Additionally, it defines a `build_extra_config` method that subclasses can
    override in order to specify extra config options.

    """    

    aliases = Dict(base_aliases)
    flags = Dict(base_flags)

    # This is a hack in order to centralize the config options inherited from
    # IPython. Rather than allowing them to be configured for each app separately,
    # this makes them non-configurable for the apps themselves. Then, in the init,
    # an instance of `BasicConfig` is created, which contains these options, and
    # their values are set on the application instance. So, to configure these
    # options, the `BasicConfig` class can be configured, rather than the 
    # application itself.
    profile = Unicode()
    overwrite = Bool()
    auto_create = Bool()
    extra_config_file = Unicode()
    log_level = 30
    copy_config_files = Bool()
    verbose_crash = Bool()
    ipython_dir = Unicode()
    log_datefmt = Unicode()
    log_format = Unicode()

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        return [BasicConfig]

    def _config_file_name_default(self):
        return u'nbgrader_config.py'

    def __init__(self, *args, **kwargs):
        super(BaseApp, self).__init__(*args, **kwargs)
        config = BasicConfig(parent=self)
        for trait in config.traits(config=True):
            setattr(self, trait, getattr(config, trait))

    def build_extra_config(self):
        pass

    @catch_config_error
    def initialize(self, argv=None):
        super(BaseApp, self).initialize(argv)
        self.stage_default_config_file()
        self.build_extra_config()


class BaseNbGraderApp(BaseApp):
    """A base class for all the nbgrader apps that depend on the nbgrader
    directory structure.

    """

    # must be overwritten by subclasses
    nbgrader_step_input = Unicode("")
    nbgrader_step_output = Unicode("")

    def _classes_default(self):
        classes = super(BaseNbGraderApp, self)._classes_default()
        classes.append(NbGraderConfig)
        return classes

    def __init__(self, *args, **kwargs):
        super(BaseNbGraderApp, self).__init__(*args, **kwargs)
        config = NbGraderConfig(parent=self)
        for traitname, trait in config.traits(config=True).items():
            setattr(self, traitname, trait)


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

    use_output_suffix = Bool(False)
    postprocessor_class = DottedOrNone('')
    notebooks = List([])
    writer_class = DottedOrNone('FilesWriter')
    output_base = Unicode('')

    def init_notebooks(self):
        # the assignment can be set via extra args
        if len(self.extra_args) > 1:
            self.log.error("Only one argument (the assignment id) may be specified")
            sys.exit(1)
        elif len(self.extra_args) == 1 and self.assignment_id != "":
            self.log.error("The assignment cannot both be specified in config and as an argument")
            sys.exit(1)
        elif len(self.extra_args) == 0 and self.assignment_id == "":
            self.log.error("An assignment id must be specified, either as an argument or with --assignment")
            sys.exit(1)
        elif len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]

        directory_structure = os.path.join(self.directory_structure, self.notebook_id + ".ipynb")
        fullglob = directory_structure.format(
            nbgrader_step=self.nbgrader_step_input,
            student_id=self.student_id,
            assignment_id=self.assignment_id,
            notebook_id=self.notebook_id
        )

        self.notebooks = glob.glob(fullglob)
        if len(self.notebooks) == 0:
            self.log.error("No notebooks were matched by '%s'", fullglob)
            sys.exit(1)

    def init_single_notebook_resources(self, notebook_filename):
        directory_structure = os.path.join(self.directory_structure, "(?P<notebook_id>.*).ipynb")
        regexp = directory_structure.format(
            nbgrader_step=self.nbgrader_step_input,
            student_id="(?P<student_id>.*)",
            assignment_id="(?P<assignment_id>.*)",
        )

        m = re.match(regexp, notebook_filename)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", notebook_filename, regexp)
        gd = m.groupdict()

        self.log.debug("Student: %s", gd['student_id'])
        self.log.debug("Assignment: %s", gd['assignment_id'])
        self.log.debug("Notebook: %s", gd['notebook_id'])

        resources = {}
        resources['profile_dir'] = self.profile_dir.location
        resources['unique_key'] = gd['notebook_id']
        resources['output_files_dir'] = '%s_files' % gd['notebook_id']

        resources['nbgrader'] = {}
        resources['nbgrader']['student'] = gd['student_id']
        resources['nbgrader']['assignment'] = gd['assignment_id']
        resources['nbgrader']['notebook'] = gd['notebook_id']
        resources['nbgrader']['db_url'] = self.db_url

        return resources

    def write_single_notebook(self, output, resources):
        # detect other files in the source directory
        source = resources['metadata']['path']
        self.writer.files = []
        for dirname, dirnames, filenames in os.walk(source):
            for filename in filenames:
                fullpath = os.path.join(dirname, filename)
                if fullpath in self.notebooks:
                    continue
                self.writer.files.append(fullpath)

        # configure the writer build directory
        self.writer.build_directory = self.directory_structure.format(
            nbgrader_step=self.nbgrader_step_output,
            student_id=resources['nbgrader']['student'],
            assignment_id=resources['nbgrader']['assignment'],
        )

        return super(BaseNbConvertApp, self).write_single_notebook(output, resources)
