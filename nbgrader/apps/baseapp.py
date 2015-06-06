#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import glob
import sys
import re
import os
import traceback
import logging
import datetime
import shutil

from tornado.log import LogFormatter

from IPython.utils.traitlets import Unicode, List, Bool, Instance, Dict, Integer
from IPython.core.application import BaseIPythonApplication
from IPython.config.application import catch_config_error
from IPython.nbconvert.nbconvertapp import NbConvertApp, DottedOrNone
from IPython.config.loader import Config
from IPython.utils.path import link_or_copy, ensure_dir_exists
from IPython.nbconvert.exporters.export import exporter_map

from nbgrader.config import BasicConfig, NbGraderConfig
from nbgrader.utils import check_directory, parse_utc, find_all_files

from textwrap import dedent
from dateutil.tz import gettz

# These are the aliases and flags for nbgrader apps that inherit only from
# BaseApp (and not BaseNbGraderApp)
base_aliases = {
    'log-level' : 'Application.log_level',
    'config' : 'BasicConfig.extra_config_file',
}
base_flags = {
    'debug': (
        {'Application' : {'log_level' : 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : 'CRITICAL'}},
        "set log level to CRITICAL (minimize logging output)"
    ),
}

def format_excepthook(etype, evaule, tb):
    traceback.print_exception(etype, evalue, tb)
    print(dedent(
        """
        If you suspect this is a nbgrader bug, please report it at:
            https://github.com/jupyter/nbgrader/issues
        """
    ), file=sys.stderr)

class BaseApp(BaseIPythonApplication):
    """A base class for all the nbgrader apps. This sets a few important defaults,
    like the IPython profile (nbgrader) and that this profile should be created
    automatically if it doesn't exist.

    Additionally, it defines a `build_extra_config` method that subclasses can
    override in order to specify extra config options.

    """

    aliases = base_aliases
    flags = base_flags

    _log_formatter_cls = LogFormatter

    def _log_level_default(self):
        return logging.INFO

    def fail(self, msg, *args):
        """Log the error msg using self.log.error and exit using sys.exit(1)."""
        self.log.error(msg, *args)
        sys.exit(1)

    verbose_crash = Bool(False)

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
    copy_config_files = Bool()
    ipython_dir = Unicode()
    log_datefmt = Unicode()
    log_format = Unicode()

    # The classes added here determine how configuration will be documented
    classes = List()

    # Basic configuration instance
    _basic_config = Instance(BasicConfig)

    def _classes_default(self):
        return [BasicConfig]

    def _config_file_name_default(self):
        return u'nbgrader_config'

    def __init__(self, *args, **kwargs):
        super(BaseApp, self).__init__(*args, **kwargs)
        self._basic_config = BasicConfig(parent=self)

    def build_extra_config(self):
        return Config()

    def excepthook(self, etype, evalue, tb):
        format_excepthook(etype, evaule, tb)

    @catch_config_error
    def initialize(self, argv=None):
        self.update_config(self.build_extra_config())
        super(BaseApp, self).initialize(argv)


# These are the aliases and flags for nbgrader apps that inherit only from
# BaseNbGraderApp (and not BaseNbConvertApp)
nbgrader_aliases = {}
nbgrader_aliases.update(base_aliases)
nbgrader_aliases.update({
    'student': 'NbGraderConfig.student_id',
    'assignment': 'NbGraderConfig.assignment_id',
    'notebook': 'NbGraderConfig.notebook_id',
    'db': 'NbGraderConfig.db_url',
    'course': 'NbGraderConfig.course_id'
})
nbgrader_flags = {}
nbgrader_flags.update(base_flags)
nbgrader_flags.update({
})
        
class BaseNbGraderApp(BaseApp):
    """A base class for all the nbgrader apps that depend on the nbgrader
    directory structure.

    """

    aliases = nbgrader_aliases
    flags = nbgrader_flags

    # these must be defined, but then will actually be populated with values from
    # the NbGraderConfig instance
    db_url = Unicode()
    student_id = Unicode()
    assignment_id = Unicode()
    notebook_id = Unicode()
    directory_structure = Unicode()
    source_directory = Unicode()
    release_directory = Unicode()
    submitted_directory = Unicode()
    autograded_directory = Unicode()
    feedback_directory = Unicode()
    course_id = Unicode()
    
    # nbgrader configuration instance
    _nbgrader_config = Instance(NbGraderConfig)

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__"
        ],
        config=True,
        help=dedent(
            """
            List of file names or file globs to be ignored when copying directories.
            """
        )
    )
    
    def _classes_default(self):
        classes = super(BaseNbGraderApp, self)._classes_default()
        classes.append(NbGraderConfig)
        return classes

    def _get_existing_timestamp(self, dest_path):
        """Get the timestamp, as a datetime object, of an existing submission."""
        timestamp_path = os.path.join(dest_path, 'timestamp.txt')
        if os.path.exists(timestamp_path):
            with open(timestamp_path, 'r') as fh:
                timestamp = fh.read().strip()
            return parse_utc(timestamp)
        else:
            return None

    def __init__(self, *args, **kwargs):
        super(BaseNbGraderApp, self).__init__(*args, **kwargs)
        self._nbgrader_config = NbGraderConfig(parent=self)

        
# These are the aliases and flags for nbgrader apps that inherit only from
# TransferApp
transfer_aliases = {}
transfer_aliases.update(nbgrader_aliases)
transfer_aliases.update({
    "timezone": "TransferApp.timezone"
})
transfer_flags = {}
transfer_flags.update(nbgrader_flags)
transfer_flags.update({
})
        
class TransferApp(BaseNbGraderApp):
    """A base class for the list, release, collect, fetch, and submit apps.
    
    All of these apps involve transfering files between an instructor or students
    files and the nbgrader exchange.
    """
    
    timezone = Unicode(
        "UTC", config=True,
        help="Timezone for recording timestamps"
    )

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z", config=True,
        help="Format string for timestamps"
    )

    def set_timestamp(self):
        """Set the timestap using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)

    exchange_directory = Unicode(
        "/srv/nbgrader/exchange",
        config=True,
        help="The nbgrader exchange directory writable to everyone. MUST be preexisting."
    )

    def ensure_exchange_directory(self):
        """See if the exchange directory exists and is writable, fail if not."""
        if not check_directory(self.exchange_directory, write=True, execute=True):
            self.fail("Unwritable directory, please contact your instructor: {}".format(self.exchange_directory))

    def init_args(self):
        pass

    @catch_config_error
    def initialize(self, argv=None):
        super(TransferApp, self).initialize(argv)
        self.init_args()
        self.ensure_exchange_directory()
        self.set_timestamp()

    def init_src(self):
        """Compute and check the source paths for the transfer."""
        raise NotImplemented
    
    def init_dest(self):
        """Compute and check the destination paths for the transfer."""
        raise NotImplemented
    
    def copy_files(self):
        """Actually to the file transfer."""
        raise NotImplemented

    def do_copy(self, src, dest):
        """Copy the src dir to the dest dir omitting the self.ignore globs."""
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.ignore))

    def start(self):
        super(TransferApp, self).start() 
        self.init_src()
        self.init_dest()
        self.copy_files()


# These are the aliases and flags for nbgrade apps that inherit from BaseNbConvertApp
nbconvert_aliases = {}
nbconvert_aliases.update(nbgrader_aliases)
nbconvert_aliases.update({
})
nbconvert_flags = {}
nbconvert_flags.update(nbgrader_flags)
nbconvert_flags.update({
    'force': (
        {'BaseNbConvertApp': {'force': True}},
        "Overwrite an assignment/submission if it already exists."
    ),
})

class BaseNbConvertApp(BaseNbGraderApp, NbConvertApp):
    """A base class for all the nbgrader apps that utilize nbconvert. This
    inherits defaults from BaseNbGraderApp, while exposing nbconvert's
    functionality of running preprocessors and writing a new file.

    The default export format is 'assignment', which is a special export format
    defined in nbgrader (see nbgrader.exporters.assignmentexporter) that
    includes a few things that nbgrader needs (such as the path to the file).

    """

    aliases = nbconvert_aliases
    flags = nbconvert_flags

    use_output_suffix = Bool(False)
    postprocessor_class = DottedOrNone('')
    notebooks = List([])
    assignments = Dict({})
    writer_class = DottedOrNone('FilesWriter')
    output_base = Unicode('')

    preprocessors = List([])

    force = Bool(False, config=True, help="Whether to overwrite existing assignments/submissions")

    permissions = Integer(
        config=True,
        help=dedent(
            """
            Permissions to set on files output by nbgrader. The default is generally
            read-only (444), with the exception of nbgrader assign, in which case the
            user also has write permission.
            """
        )
    )

    def _permissions_default(self):
        return 444

    def _classes_default(self):
        classes = super(BaseNbConvertApp, self)._classes_default()
        for pp in self.preprocessors:
            if len(pp.class_traits(config=True)) > 0:
                classes.append(pp)
        return classes

    @property
    def _input_directory(self):
        raise NotImplementedError

    @property
    def _output_directory(self):
        raise NotImplementedError

    def _format_source(self, assignment_id, student_id):
        return self.directory_structure.format(
            nbgrader_step=self._input_directory,
            student_id=student_id,
            assignment_id=assignment_id
        )

    def _format_dest(self, assignment_id, student_id):
        return self.directory_structure.format(
            nbgrader_step=self._output_directory,
            student_id=student_id,
            assignment_id=assignment_id
        )

    def build_extra_config(self):
        extra_config = super(BaseNbConvertApp, self).build_extra_config()
        extra_config.Exporter.default_preprocessors = self.preprocessors
        return extra_config

    def init_notebooks(self):
        # the assignment can be set via extra args
        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]

        self.assignments = {}
        self.notebooks = []
        fullglob = self._format_source(self.assignment_id, self.student_id)
        for assignment in glob.glob(fullglob):
            self.assignments[assignment] = glob.glob(os.path.join(assignment, self.notebook_id + ".ipynb"))
            if len(self.assignments[assignment]) == 0:
                self.fail("No notebooks were matched in '%s'", assignment)

        if len(self.assignments) == 0:
            self.fail("No notebooks were matched by '%s'", fullglob)

    def init_single_notebook_resources(self, notebook_filename):
        regexp = os.path.join(
            self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)"),
            "(?P<notebook_id>.*).ipynb")

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
        # configure the writer build directory
        self.writer.build_directory = self._format_dest(
            resources['nbgrader']['assignment'], resources['nbgrader']['student'])
        return super(BaseNbConvertApp, self).write_single_notebook(output, resources)

    def init_destination(self, assignment_id, student_id):
        """Initialize the destination for an assignment. Returns whether the
        assignment should actually be processed or not (i.e. whether the
        initialization was successful).

        """
        dest = os.path.normpath(self._format_dest(assignment_id, student_id))

        # the destination doesn't exist, so we haven't processed it
        if self.notebook_id == "*":
            if not os.path.exists(dest):
                return True
        else:
            # if any of the notebooks don't exist, then we want to process them
            for notebook in self.notebooks:
                filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                path = os.path.join(dest, filename)
                if not os.path.exists(path):
                    return True

        # if we have specified --force, then always remove existing stuff
        if self.force:
            if self.notebook_id == "*":
                self.log.warning("Removing existing assignment: {}".format(dest))
                shutil.rmtree(dest)
            else:
                for notebook in self.notebooks:
                    filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                    path = os.path.join(dest, filename)
                    if os.path.exists(path):
                        self.log.warning("Removing existing notebook: {}".format(path))
                        os.remove(path)
            return True

        src = self._format_source(assignment_id, student_id)
        new_timestamp = self._get_existing_timestamp(src)
        old_timestamp = self._get_existing_timestamp(dest)

        # if --force hasn't been specified, but the source assignment is newer,
        # then we want to overwrite it
        if new_timestamp is not None and old_timestamp is not None and new_timestamp > old_timestamp:
            if self.notebook_id == "*":
                self.log.warning("Updating existing assignment: {}".format(dest))
                shutil.rmtree(dest)
            else:
                for notebook in self.notebooks:
                    filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                    path = os.path.join(dest, filename)
                    if os.path.exists(path):
                        self.log.warning("Updating existing notebook: {}".format(path))
                        os.remove(path)
            return True

        # otherwise, we should skip the assignment
        self.log.info("Skipping existing assignment: {}".format(dest))
        return False

    def init_assignment(self, assignment_id, student_id):
        """Initializes resources/dependencies/etc. that are common to all
        notebooks in an assignment.

        """
        source = self._format_source(assignment_id, student_id)
        dest = self._format_dest(assignment_id, student_id)

        # detect other files in the source directory
        for filename in find_all_files(source, self.ignore + ["*.ipynb"]):
            # Make sure folder exists.
            path = os.path.join(dest, os.path.relpath(filename, source))
            ensure_dir_exists(os.path.dirname(path))

            # Copy if destination is different.
            if not os.path.normpath(path) == os.path.normpath(filename):
                self.log.info("Linking %s -> %s", filename, path)
                link_or_copy(filename, path)

    def set_permissions(self, assignment_id, student_id):
        self.log.info("Setting destination file permissions to %s", self.permissions)
        dest = os.path.normpath(self._format_dest(assignment_id, student_id))
        permissions = int(str(self.permissions), 8)
        for dirname, dirnames, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), permissions)

    def convert_notebooks(self):
        for assignment in sorted(self.assignments.keys()):
            # initialize the list of notebooks and the exporter
            self.notebooks = self.assignments[assignment]
            self.exporter = exporter_map[self.export_format](config=self.config)

            # parse out the assignment and student ids
            regexp = self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)")
            m = re.match(regexp, assignment)
            if m is None:
                raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
            gd = m.groupdict()

            try:
                # determine whether we actually even want to process this submission
                should_process = self.init_destination(gd['assignment_id'], gd['student_id'])
                if not should_process:
                    continue

                # initialize the destination and convert
                self.init_assignment(gd['assignment_id'], gd['student_id'])
                super(BaseNbConvertApp, self).convert_notebooks()
                self.set_permissions(gd['assignment_id'], gd['student_id'])

            except:
                self.log.error("There was an error processing assignment: %s", assignment)

                dest = os.path.normpath(self._format_dest(gd['assignment_id'], gd['student_id']))
                if self.notebook_id == "*":
                    if os.path.exists(dest):
                        self.log.warning("Removing failed assignment: {}".format(dest))
                        shutil.rmtree(dest)
                else:
                    for notebook in self.notebooks:
                        filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                        path = os.path.join(dest, filename)
                        if os.path.exists(path):
                            self.log.warning("Removing failed notebook: {}".format(path))
                            os.remove(path)

                raise
