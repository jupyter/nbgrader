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

from dateutil.tz import gettz
from jupyter_core.application import JupyterApp
from jupyter_core.paths import jupyter_data_dir
from nbconvert.exporters.export import exporter_map
from nbconvert.nbconvertapp import NbConvertApp, DottedOrNone
from textwrap import dedent
from tornado.log import LogFormatter
from traitlets import Unicode, List, Bool, Dict, Integer, observe, default
from traitlets.config.application import catch_config_error
from traitlets.config.loader import Config

from ..utils import check_directory, parse_utc, find_all_files, full_split, rmtree, remove
from ..preprocessors.execute import UnresponsiveKernelError


nbgrader_aliases = {
    'log-level' : 'Application.log_level',
    'student': 'NbGrader.student_id',
    'assignment': 'NbGrader.assignment_id',
    'notebook': 'NbGrader.notebook_id',
    'db': 'NbGrader.db_url',
    'course': 'NbGrader.course_id',
    'course-dir': 'NbGrader.course_directory'
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

    db_url = Unicode(
        "",
        help=dedent(
            """
            URL to the database. Defaults to sqlite:///<course_directory>/gradebook.db,
            where <course_directory> is another configurable variable.
            """
        )
    ).tag(config=True)

    @default("db_url")
    def _db_url_default(self):
        return "sqlite:///{}".format(
            os.path.abspath(os.path.join(self.course_directory, "gradebook.db")))

    student_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match student IDs. This can be changed to filter by
            student. Note: this is always changed to '.' when running `nbgrader
            assign`, as the assign step doesn't have any student ID associated
            with it.
            """
        )
    ).tag(config=True)

    assignment_id = Unicode(
        "",
        help=dedent(
            """
            The assignment name. This MUST be specified, either by setting the
            config option, passing an argument on the command line, or using the
            --assignment option on the command line.
            """
        )
    ).tag(config=True)

    notebook_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match notebook names, excluding the '.ipynb' extension.
            This can be changed to filter by notebook.
            """
        )
    ).tag(config=True)

    directory_structure = Unicode(
        os.path.join("{nbgrader_step}", "{student_id}", "{assignment_id}"),
        help=dedent(
            """
            Format string for the directory structure that nbgrader works
            over during the grading process. This MUST contain named keys for
            'nbgrader_step', 'student_id', and 'assignment_id'. It SHOULD NOT
            contain a key for 'notebook_id', as this will be automatically joined
            with the rest of the path.
            """
        )
    ).tag(config=True)

    source_directory = Unicode(
        'source',
        help=dedent(
            """
            The name of the directory that contains the master/instructor
            version of assignments. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    release_directory = Unicode(
        'release',
        help=dedent(
            """
            The name of the directory that contains the version of the
            assignment that will be released to students. This corresponds to
            the `nbgrader_step` variable in the `directory_structure` config
            option.
            """
        )
    ).tag(config=True)

    submitted_directory = Unicode(
        'submitted',
        help=dedent(
            """
            The name of the directory that contains assignments that have been
            submitted by students for grading. This corresponds to the
            `nbgrader_step` variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    autograded_directory = Unicode(
        'autograded',
        help=dedent(
            """
            The name of the directory that contains assignment submissions after
            they have been autograded. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    feedback_directory = Unicode(
        'feedback',
        help=dedent(
            """
            The name of the directory that contains assignment feedback after
            grading has been completed. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    course_id = Unicode(
        '',
        help=dedent(
            """
            A key that is unique per instructor and course. This MUST be
            specified, either by setting the config option, or using the
            --course option on the command line.
            """
        )
    ).tag(config=True)

    course_directory = Unicode(
        '',
        help=dedent(
            """
            The root directory for the course files (that includes the `source`,
            `release`, `submitted`, `autograded`, etc. directories). Defaults to
            the current working directory.
            """
        )
    ).tag(config=True)

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

    @default("course_directory")
    def _course_directory_default(self):
        return os.getcwd()

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__"
        ],
        help=dedent(
            """
            List of file names or file globs to be ignored when copying directories.
            """
        )
    ).tag(config=True)

    verbose_crash = Bool(False)

    # The classes added here determine how configuration will be documented
    classes = List()

    @default("classes")
    def _classes_default(self):
        return [NbGrader]

    @default("config_file_name")
    def _config_file_name_default(self):
        return u'nbgrader_config'

    def _get_existing_timestamp(self, dest_path):
        """Get the timestamp, as a datetime object, of an existing submission."""
        timestamp_path = os.path.join(dest_path, 'timestamp.txt')
        if os.path.exists(timestamp_path):
            with open(timestamp_path, 'r') as fh:
                timestamp = fh.read().strip()
            if not timestamp:
                self.log.warning(
                    "Empty timestamp file: {}".format(timestamp_path))
                return None
            try:
                return parse_utc(timestamp)
            except ValueError:
                self.fail(
                    "Invalid timestamp string: {}".format(timestamp_path))
        else:
            return None

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

        super(NbGrader, self)._load_config(cfg, **kwargs)

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

    def _format_path(self, nbgrader_step, student_id, assignment_id, escape=False):

        kwargs = dict(
            nbgrader_step=nbgrader_step,
            student_id=student_id,
            assignment_id=assignment_id
        )

        if escape:
            base = re.escape(self.course_directory)
            structure = [x.format(**kwargs) for x in full_split(self.directory_structure)]
            path = re.escape(os.path.sep).join([base] + structure)
        else:
            path = os.path.join(self.course_directory, self.directory_structure).format(**kwargs)

        return path

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


# These are the aliases and flags for nbgrader apps that inherit only from
# TransferApp
transfer_aliases = {}
transfer_aliases.update(nbgrader_aliases)
transfer_aliases.update({
    "timezone": "TransferApp.timezone",
})
transfer_flags = {}
transfer_flags.update(nbgrader_flags)
transfer_flags.update({
})

class TransferApp(NbGrader):
    """A base class for the list, release, collect, fetch, and submit apps.

    All of these apps involve transfering files between an instructor or students
    files and the nbgrader exchange.
    """

    timezone = Unicode(
        "UTC",
        help="Timezone for recording timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z",
        help="Format string for timestamps"
    ).tag(config=True)

    exchange_directory = Unicode(
        "/srv/nbgrader/exchange",
        help="The nbgrader exchange directory writable to everyone. MUST be preexisting."
    ).tag(config=True)

    cache_directory = Unicode(
        "",
        help="Local cache directory for nbgrader submit and nbgrader list. Defaults to $JUPYTER_DATA_DIR/nbgrader_cache"
    ).tag(config=True)

    path_includes_course = Bool(
        False,
        help=dedent(
            """
            Whether the path for fetching/submitting  assignments should be
            prefixed with the course name. If this is `False`, then the path
            will be something like `./ps1`. If this is `True`, then the path
            will be something like `./course123/ps1`.
            """
        )
    ).tag(config=True)

    @default("cache_directory")
    def _cache_directory_default(self):
        return os.path.join(jupyter_data_dir(), 'nbgrader_cache')

    def set_timestamp(self):
        """Set the timestap using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)

    def ensure_exchange_directory(self):
        """See if the exchange directory exists and is writable, fail if not."""
        if not check_directory(self.exchange_directory, write=True, execute=True):
            self.fail("Unwritable directory, please contact your instructor: {}".format(self.exchange_directory))

    @catch_config_error
    def initialize(self, argv=None):
        if sys.platform == 'win32':
            self.fail("Sorry, %s is not available on Windows.", self.name.replace("-", " "))

        super(TransferApp, self).initialize(argv)
        self.ensure_exchange_directory()
        self.set_timestamp()

    def init_src(self):
        """Compute and check the source paths for the transfer."""
        raise NotImplementedError

    def init_dest(self):
        """Compute and check the destination paths for the transfer."""
        raise NotImplementedError

    def copy_files(self):
        """Actually do the file transfer."""
        raise NotImplementedError

    def set_perms(self, dest, perms):
        all_dirs = []
        for dirname, dirnames, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), perms)
            all_dirs.append(dirname)

        for dirname in all_dirs[::-1]:
            os.chmod(dirname, perms)

    def do_copy(self, src, dest, perms=None):
        """Copy the src dir to the dest dir omitting the self.ignore globs."""
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.ignore))
        if perms:
            self.set_perms(dest, perms=perms)

    def start(self):
        super(TransferApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

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
        return self._format_path(self._input_directory, student_id, assignment_id, escape=escape)

    def _format_dest(self, assignment_id, student_id, escape=False):
        return self._format_path(self._output_directory, student_id, assignment_id, escape=escape)

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
        new_timestamp = self._get_existing_timestamp(src)
        old_timestamp = self._get_existing_timestamp(dest)

        # if --force hasn't been specified, but the source assignment is newer,
        # then we want to overwrite it
        if new_timestamp is not None and old_timestamp is not None and new_timestamp > old_timestamp:
            if self.notebook_id == "*":
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
        for filename in find_all_files(source, self.ignore + ["*.ipynb"]):
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
        for dirname, dirnames, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), permissions)

    def convert_notebooks(self):
        errors = []

        def _handle_failure(gd):
            dest = os.path.normpath(self._format_dest(gd['assignment_id'], gd['student_id']))
            if self.notebook_id == "*":
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
