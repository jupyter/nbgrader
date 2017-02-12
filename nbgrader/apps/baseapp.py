#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import glob
import sys
import re
import os
import traceback
import logging
import shutil

from jupyter_core.application import JupyterApp
from nbconvert.exporters.export import exporter_map
from nbconvert.nbconvertapp import NbConvertApp, DottedOrNone
from textwrap import dedent
from tornado.log import LogFormatter
from traitlets import Unicode, List, Bool, Dict, Integer, Instance, default
from traitlets.config.application import catch_config_error
from traitlets.config.loader import Config

from ..utils import find_all_files, rmtree, remove
from ..preprocessors.execute import UnresponsiveKernelError
from ..coursedir import CourseDirectory


nbgrader_aliases = {
    'log-level' : 'Application.log_level',
    'student': 'CourseDirectory.student_id',
    'assignment': 'CourseDirectory.assignment_id',
    'notebook': 'CourseDirectory.notebook_id',
    'db': 'CourseDirectory.db_url',
    'course-dir': 'CourseDirectory.root'
}
nbgrader_flags = {
    'debug': (
        {'Application' : {'log_level' : 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : 'CRITICAL'}},
        "set log level to CRITICAL (minimize logging output)"
    ),
}

def format_excepthook(etype, evalue, tb):
    traceback.print_exception(etype, evalue, tb)
    print(dedent(
        """
        If you suspect this is a nbgrader bug, please report it at:
            https://github.com/jupyter/nbgrader/issues
        """
    ), file=sys.stderr)


class NbGrader(JupyterApp):
    """A base class for all the nbgrader apps."""

    aliases = nbgrader_aliases
    flags = nbgrader_flags

    _log_formatter_cls = LogFormatter

    @default("log_level")
    def _log_level_default(self):
        return logging.INFO

    @default("log_datefmt")
    def _log_datefmt_default(self):
        return "%Y-%m-%d %H:%M:%S"

    @default("log_format")
    def _log_format_default(self):
        return "%(color)s[%(name)s | %(levelname)s]%(end_color)s %(message)s"

    logfile = Unicode(
        ".nbgrader.log",
        help=dedent(
            """
            Name of the logfile to log to.
            """
        )
    ).tag(config=True)

    def init_logging(self, handler_class, handler_args, color=True, subapps=False):
        handler = handler_class(*handler_args)

        if color:
            log_format = self.log_format
        else:
            log_format = self.log_format.replace("%(color)s", "").replace("%(end_color)s", "")

        _formatter = self._log_formatter_cls(
            fmt=log_format,
            datefmt=self.log_datefmt)
        handler.setFormatter(_formatter)

        self.log.addHandler(handler)

        if subapps and self.subapp:
            self.subapp.init_logging(handler_class, handler_args, color=color, subapps=subapps)

    def deinit_logging(self):
        if len(self.log.handlers) > 1:
            for handler in self.log.handlers[1:]:
                handler.close()
                self.log.removeHandler(handler)

    db_assignments = List(
        help=dedent(
            """
            A list of assignments that will be created in the database. Each
            item in the list should be a dictionary with the following keys:

                - name
                - duedate (optional)

            The values will be stored in the database. Please see the API
            documentation on the `Assignment` database model for details on
            these fields.
            """
        )
    ).tag(config=True)

    db_students = List(
        help=dedent(
            """
            A list of student that will be created in the database. Each
            item in the list should be a dictionary with the following keys:

                - id
                - first_name (optional)
                - last_name (optional)
                - email (optional)

            The values will be stored in the database. Please see the API
            documentation on the `Student` database model for details on
            these fields.
            """
        )
    ).tag(config=True)

    coursedir = Instance(CourseDirectory, allow_none=True)
    verbose_crash = Bool(False)

    # The classes added here determine how configuration will be documented
    classes = List()

    @default("classes")
    def _classes_default(self):
        return [NbGrader, CourseDirectory]

    @default("config_file_name")
    def _config_file_name_default(self):
        return u'nbgrader_config'

    def _load_config(self, cfg, **kwargs):
        if 'NbGraderConfig' in cfg:
            self.log.warn(
                "Use NbGrader in config, not NbGraderConfig. Outdated config:\n%s",
                '\n'.join(
                    'NbGraderConfig.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.NbGraderConfig.items()
                )
            )
            cfg.NbGrader.merge(cfg.NbGraderConfig)
            del cfg.NbGraderConfig

        if 'BasicConfig' in cfg:
            self.log.warn(
                "Use NbGrader in config, not BasicConfig. Outdated config:\n%s",
                '\n'.join(
                    'BasicConfig.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BasicConfig.items()
                )
            )
            cfg.NbGrader.merge(cfg.BasicConfig)
            del cfg.BasicConfig

        if 'BaseNbGraderApp' in cfg:
            self.log.warn(
                "Use NbGrader in config, not BaseNbGraderApp. Outdated config:\n%s",
                '\n'.join(
                    'BaseNbGraderApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BaseNbGraderApp.items()
                )
            )
            cfg.NbGrader.merge(cfg.BaseNbGraderApp)
            del cfg.BaseNbGraderApp

        if 'BaseApp' in cfg:
            self.log.warn(
                "Use NbGrader in config, not BaseApp. Outdated config:\n%s",
                '\n'.join(
                    'BaseApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BaseApp.items()
                )
            )
            cfg.NbGrader.merge(cfg.BaseApp)
            del cfg.BaseApp

        coursedir_options = [
            ("student_id", "student_id"),
            ("assignment_id", "assignment_id"),
            ("notebook_id", "notebook_id"),
            ("directory_structure", "directory_structure"),
            ("source_directory", "source_directory"),
            ("release_directory", "release_directory"),
            ("submitted_directory", "submitted_directory"),
            ("autograded_directory", "autograded_directory"),
            ("feedback_directory", "feedback_directory"),
            ("db_url", "db_url"),
            ("course_directory", "root"),
            ("ignore", "ignore")
        ]

        for old_opt, new_opt in coursedir_options:
            if old_opt in cfg.NbGrader:
                self.log.warn("Outdated config: use CourseDirectory.{} rather than NbGrader.{}".format(new_opt, old_opt))
                setattr(cfg.CourseDirectory, new_opt, cfg.NbGrader[old_opt])
                delattr(cfg.NbGrader, old_opt)

        if "course_id" in cfg.NbGrader:
            self.log.warn("Outdated config: use Exchange.course_id rather than NbGrader.course_id")
            cfg.Exchange.course_id = cfg.NbGrader.course_id
            del cfg.NbGrader.course_id

        exchange_options = [
            ("timezone", "timezone"),
            ("timestamp_format", "timestamp_format"),
            ("exchange_directory", "root"),
            ("cache_directory", "cache")
        ]

        for old_opt, new_opt in exchange_options:
            if old_opt in cfg.TransferApp:
                self.log.warn("Outdated config: use Exchange.{} rather than TransferApp.{}".format(new_opt, old_opt))
                setattr(cfg.Exchange, new_opt, cfg.TransferApp[old_opt])
                delattr(cfg.TransferApp, old_opt)

        if 'TransferApp' in cfg and cfg.TransferApp:
            self.log.warn(
                "Use Exchange in config, not TransferApp. Outdated config:\n%s",
                '\n'.join(
                    'TransferApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.TransferApp.items()
                )
            )
            cfg.Exchange.merge(cfg.TransferApp)
            del cfg.TransferApp

        super(NbGrader, self)._load_config(cfg, **kwargs)
        if self.coursedir:
            self.coursedir._load_config(cfg)

    def fail(self, msg, *args):
        """Log the error msg using self.log.error and exit using sys.exit(1)."""
        self.log.error(msg, *args)
        sys.exit(1)

    def build_extra_config(self):
        return Config()

    def excepthook(self, etype, evalue, tb):
        format_excepthook(etype, evalue, tb)

    @catch_config_error
    def initialize(self, argv=None):
        self.update_config(self.build_extra_config())
        if self.logfile:
            self.init_logging(logging.FileHandler, [self.logfile], color=False)
        self.init_syspath()
        self.coursedir = CourseDirectory(parent=self)
        super(NbGrader, self).initialize(argv)

    def init_syspath(self):
        """Add the cwd to the sys.path ($PYTHONPATH)"""
        sys.path.insert(0, os.getcwd())

    def reset(self):
        # stop logging
        self.deinit_logging()

        # recursively reset all subapps
        if self.subapp:
            self.subapp.reset()

        # clear the instance
        self.clear_instance()

    def load_config_file(self, **kwargs):
        """Load the config file.
        By default, errors in loading config are handled, and a warning
        printed on screen. For testing, the suppress_errors option is set
        to False, so errors will make tests fail.
        """
        if self.config_file:
            paths = [os.path.abspath("{}.py".format(self.config_file))]
        else:
            paths = [os.path.join(x, "{}.py".format(self.config_file_name)) for x in self.config_file_paths]

        if not any(os.path.exists(x) for x in paths):
            self.log.warn("No nbgrader_config.py file found (rerun with --debug to see where nbgrader is looking)")

        super(NbGrader, self).load_config_file(**kwargs)


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

class BaseNbConvertApp(NbGrader, NbConvertApp):
    """A base class for all the nbgrader apps that utilize nbconvert. This
    inherits defaults from NbGrader, while exposing nbconvert's
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

    force = Bool(False, help="Whether to overwrite existing assignments/submissions").tag(config=True)

    permissions = Integer(
        help=dedent(
            """
            Permissions to set on files output by nbgrader. The default is generally
            read-only (444), with the exception of nbgrader assign, in which case the
            user also has write permission.
            """
        )
    ).tag(config=True)

    @default("permissions")
    def _permissions_default(self):
        return 444

    @default("classes")
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

    def _format_source(self, assignment_id, student_id, escape=False):
        return self.coursedir.format_path(self._input_directory, student_id, assignment_id, escape=escape)

    def _format_dest(self, assignment_id, student_id, escape=False):
        return self.coursedir.format_path(self._output_directory, student_id, assignment_id, escape=escape)

    def build_extra_config(self):
        extra_config = super(BaseNbConvertApp, self).build_extra_config()
        extra_config.Exporter.default_preprocessors = self.preprocessors
        return extra_config

    def init_notebooks(self):
        # the assignment can be set via extra args
        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.coursedir.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]

        self.assignments = {}
        self.notebooks = []
        fullglob = self._format_source(self.coursedir.assignment_id, self.coursedir.student_id)
        for assignment in glob.glob(fullglob):
            self.assignments[assignment] = glob.glob(os.path.join(assignment, self.coursedir.notebook_id + ".ipynb"))
            if len(self.assignments[assignment]) == 0:
                self.fail("No notebooks were matched in '%s'", assignment)

        if len(self.assignments) == 0:
            self.fail("No notebooks were matched by '%s'", fullglob)

    def init_single_notebook_resources(self, notebook_filename):
        regexp = re.escape(os.path.sep).join([
            self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)", escape=True),
            "(?P<notebook_id>.*).ipynb"
        ])

        m = re.match(regexp, notebook_filename)
        if m is None:
            self.fail("Could not match '%s' with regexp '%s'", notebook_filename, regexp)
        gd = m.groupdict()

        self.log.debug("Student: %s", gd['student_id'])
        self.log.debug("Assignment: %s", gd['assignment_id'])
        self.log.debug("Notebook: %s", gd['notebook_id'])

        resources = {}
        resources['unique_key'] = gd['notebook_id']
        resources['output_files_dir'] = '%s_files' % gd['notebook_id']

        resources['nbgrader'] = {}
        resources['nbgrader']['student'] = gd['student_id']
        resources['nbgrader']['assignment'] = gd['assignment_id']
        resources['nbgrader']['notebook'] = gd['notebook_id']
        resources['nbgrader']['db_url'] = self.coursedir.db_url

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
        if self.coursedir.notebook_id == "*":
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
            if self.coursedir.notebook_id == "*":
                self.log.warning("Removing existing assignment: {}".format(dest))
                rmtree(dest)
            else:
                for notebook in self.notebooks:
                    filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                    path = os.path.join(dest, filename)
                    if os.path.exists(path):
                        self.log.warning("Removing existing notebook: {}".format(path))
                        remove(path)
            return True

        src = self._format_source(assignment_id, student_id)
        new_timestamp = self.coursedir.get_existing_timestamp(src)
        old_timestamp = self.coursedir.get_existing_timestamp(dest)

        # if --force hasn't been specified, but the source assignment is newer,
        # then we want to overwrite it
        if new_timestamp is not None and old_timestamp is not None and new_timestamp > old_timestamp:
            if self.coursedir.notebook_id == "*":
                self.log.warning("Updating existing assignment: {}".format(dest))
                rmtree(dest)
            else:
                for notebook in self.notebooks:
                    filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                    path = os.path.join(dest, filename)
                    if os.path.exists(path):
                        self.log.warning("Updating existing notebook: {}".format(path))
                        remove(path)
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
        for filename in find_all_files(source, self.coursedir.ignore + ["*.ipynb"]):
            # Make sure folder exists.
            path = os.path.join(dest, os.path.relpath(filename, source))
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            if os.path.exists(path):
                remove(path)
            self.log.info("Copying %s -> %s", filename, path)
            shutil.copy(filename, path)

    def set_permissions(self, assignment_id, student_id):
        self.log.info("Setting destination file permissions to %s", self.permissions)
        dest = os.path.normpath(self._format_dest(assignment_id, student_id))
        permissions = int(str(self.permissions), 8)
        for dirname, _, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), permissions)

    def convert_notebooks(self):
        errors = []

        def _handle_failure(gd):
            dest = os.path.normpath(self._format_dest(gd['assignment_id'], gd['student_id']))
            if self.coursedir.notebook_id == "*":
                if os.path.exists(dest):
                    self.log.warning("Removing failed assignment: {}".format(dest))
                    rmtree(dest)
            else:
                for notebook in self.notebooks:
                    filename = os.path.splitext(os.path.basename(notebook))[0] + self.exporter.file_extension
                    path = os.path.join(dest, filename)
                    if os.path.exists(path):
                        self.log.warning("Removing failed notebook: {}".format(path))
                        remove(path)

        for assignment in sorted(self.assignments.keys()):
            # initialize the list of notebooks and the exporter
            self.notebooks = sorted(self.assignments[assignment])
            self.exporter = exporter_map[self.export_format](config=self.config)

            # parse out the assignment and student ids
            regexp = self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)", escape=True)
            m = re.match(regexp, assignment)
            if m is None:
                self.fail("Could not match '%s' with regexp '%s'", assignment, regexp)
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

            except UnresponsiveKernelError:
                self.log.error(
                    "While processing assignment %s, the kernel became "
                    "unresponsive and we could not interrupt it. This probably "
                    "means that the students' code has an infinite loop that "
                    "consumes a lot of memory or something similar. nbgrader "
                    "doesn't know how to deal with this problem, so you will "
                    "have to manually edit the students' code (for example, to "
                    "just throw an error rather than enter an infinite loop). ",
                    assignment)
                errors.append((gd['assignment_id'], gd['student_id']))
                _handle_failure(gd)

            except Exception:
                self.log.error("There was an error processing assignment: %s", assignment)
                self.log.error(traceback.format_exc())
                errors.append((gd['assignment_id'], gd['student_id']))
                _handle_failure(gd)

        if len(errors) > 0:
            for assignment_id, student_id in errors:
                self.log.error(
                    "There was an error processing assignment '{}' for student '{}'".format(
                        assignment_id, student_id))

            if self.logfile:
                self.fail(
                    "Please see the error log ({}) for details on the specific "
                    "errors on the above failures.".format(self.logfile))
