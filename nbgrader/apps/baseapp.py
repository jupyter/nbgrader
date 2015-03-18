#!/usr/bin/env python
# encoding: utf-8

import logging
import glob
import sys
import re
import os
from textwrap import dedent

from IPython.utils.traitlets import Unicode, List, Bool, Dict
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.config.application import catch_config_error
from IPython.nbconvert.nbconvertapp import NbConvertApp

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseApp (and not BaseNbGraderApp)
base_aliases = {
    'log-level' : 'Application.log_level',
    'config' : 'BaseIPythonApplication.extra_config_file',
}
base_flags = {
    'debug': (
        {'Application' : {'log_level' : logging.DEBUG}},
        "set log level to logging.DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : logging.CRITICAL}},
        "set log level to logging.CRITICAL (minimize logging output)"
    ),
}

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseNbGraderApp (and not BaseNbConvertApp)
nbgrader_aliases = {}
nbgrader_aliases.update(base_aliases)
nbgrader_aliases.update({
    'student': 'BaseNbGraderApp.student_id',
    'assignment': 'BaseNbGraderApp.assignment_id',
    'notebook': 'BaseNbGraderApp.notebook_id',
    'db': 'BaseNbGraderApp.db_url'
})
nbgrader_flags = {}
nbgrader_flags.update(base_flags)
nbgrader_flags.update({
    'debug': (
        {'Application' : {'log_level' : logging.DEBUG}},
        "set log level to logging.DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : logging.CRITICAL}},
        "set log level to logging.CRITICAL (minimize logging output)"
    ),
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

    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to the database")

    student_id = Unicode(
        "*",
        config=True,
        help=dedent(
            """
            File glob to match student ids. This can be changed to filter by 
            student id.
            """
        )
    )

    assignment_id = Unicode(
        "",
        config=True,
        help=dedent(
            """
            File glob to match assignment names. This can be changed to filter 
            by assignment id.
            """
        )
    )

    notebook_id = Unicode(
        "*",
        config=True,
        help=dedent(
            """
            File glob to match notebook ids, excluding the '.ipynb' extension. 
            This can be changed to filter by notebook id.
            """
        )
    )

    directory_structure = Unicode(
        "{nbgrader_step}/{student_id}/{assignment_id}",
        config=True,
        help=dedent(
            """
            Format string for the directory structure that nbgrader works 
            over during the grading process. This MUST contain named keys for 
            'nbgrader_step', 'student_id', and 'assignment_id'.
            """
        )
    )


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

    def _export_format_default(self):
        return 'notebook'

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
