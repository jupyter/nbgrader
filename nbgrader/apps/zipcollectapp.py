import os
import re
import sys
import shutil
import datetime

from dateutil.tz import gettz
from textwrap import dedent
from traitlets import Bool, Instance, Type, Unicode
from traitlets.config.application import catch_config_error, default

from .baseapp import NbGrader

from ..api import open_gradebook, MissingEntry
from ..plugins import BasePlugin, ExtractorPlugin, FileNameCollectorPlugin
from ..plugins.zipcollect import CollectInfo
from ..utils import check_directory, full_split, rmtree, parse_utc
from ..utils import find_all_notebooks

aliases = {
    'log-level': 'Application.log_level',
    'collector': 'ZipCollectApp.collector_plugin',
    'zip_ext': 'ExtractorPlugin.zip_ext',
}
flags = {
    'debug': (
        {'Application': {'log_level': 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
    'force': (
        {
            'ZipCollectApp': {'force': True},
            'ExtractorPlugin': {'force': True}
        },
        "Force overwrite of existing files."
    ),
    'strict': (
        {'ZipCollectApp': {'strict': True}},
        "Skip submitted notebooks with invalid names."
    ),
}


class ZipCollectApp(NbGrader):

    name = u'nbgrader-zip-collect'
    description = u'Collect assignments from archives (zip files).'

    aliases = aliases
    flags = flags

    examples = """
        Collect assignment submissions from files and/or archives (zip) files
        manually downloaded from a LMS. For the usage of instructors.

        This command is run from the top-level nbgrader folder. In order to
        facilitate the collect process, nbgrader places some constraints on how
        the manually downloaded archive (zip) files must be structured. By
        default, the directory structure must look like this:

            {downloaded}/{assignment_id}/{collect_step}

        where `downloaded` is the main directory, `assignment_id` is the name
        of the assignment and `collect_step` is the step in the collect
        process.

        Manually downloaded assignment submissions files and/or archives (zip)
        files must be placed in the `archive_directory`:

            {downloaded}/{assignment_id}/{archive_directory}

        It is expected that the instructor has already created this directory
        and placed the downloaded assignment submissions files and/or archives
        (zip) files in this directory.

        Archive (zip) files in the `archive_directory` will be extracted, and
        any non-archive files will be copied, to the `extracted_directory`:

            {downloaded}/{assignment_id}/{extracted_directory}

        After which the files in the `extracted_directory` will be collected
        and copied into the students `submitted_directory`:

            {submitted_directory}/{student_id}/{assignment_id}/{notebook_id}.ipynb

        By default the collection of files in the `extracted_directory` is
        managed via the :class:`~nbgrader.plugins.zipcollect.FileNameProcessor`
        plugin. Each filename is sent to the plugin, which in turn returns an
        object containing the `student_id`, `file_id`, `first_name`,
        `last_name`, `email`, and `timestamp` data. For more information run:

            nbgrader zip_collect --help-all

        To change the default plugin, you will need a class that inherits from
        :class:`~nbgrader.plugins.zipcollect.FileNameProcessor`. If your
        exporter is named `MyCustomProcessor` and is saved in the file
        `myprocessor.py`, then:

            nbgrader zip_collect --processor=myprocessor.MyCustomProcessor

        """

    force = Bool(
        default_value=False,
        help="Force overwrite of existing files."
    ).tag(config=True)

    strict = Bool(
        default_value=False,
        help="Skip submitted notebooks with invalid names."
    ).tag(config=True)

    collect_directory_structure = Unicode(
        os.path.join(
            "{downloaded}", "{assignment_id}", "{collect_step}"),
        help=dedent(
            """
            Format string for the directory structure that nbgrader works over
            during the zip collect process. This MUST contain named keys for
            'downloaded', 'assignment_id', and 'collect_step'.
            """
        )
    ).tag(config=True)

    downloaded_directory = Unicode(
        'downloaded',
        help=dedent(
            """
            The main directory that corresponds to the `downloaded` variable in
            the `collect_structure` config option.
            """
        )
    ).tag(config=True)

    archive_directory = Unicode(
        'archive',
        help=dedent(
            """
            The name of the directory that contains assignment submission files
            and/or archives (zip) files manually downloaded from a LMS. This
            corresponds to the `collect_step` variable in the
            `collect_structure` config option.
            """
        )
    ).tag(config=True)

    extracted_directory = Unicode(
        'extracted',
        help=dedent(
            """
            The name of the directory that contains assignment submission files
            extracted or copied from the `archive_directory`. This corresponds
            to the `collect_step` variable in the `collect_structure` config
            option.
            """
        )
    ).tag(config=True)

    timezone = Unicode(
        "UTC",
        help="Timezone for recording timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z",
        help="Format string for timestamps"
    ).tag(config=True)

    extractor_plugin = Type(
        ExtractorPlugin,
        klass=BasePlugin,
        help=dedent(
            """
            The plugin class for extracting the archive files in the
            `archive_directory`.
            """
        )
    ).tag(config=True)

    collector_plugin = Type(
        FileNameCollectorPlugin,
        klass=BasePlugin,
        help=dedent(
            """
            The plugin class for processing the submitted file names after
            they have been extracted into the `extracted_directory`.
            """
        )
    ).tag(config=True)

    collector_plugin_inst = Instance(FileNameCollectorPlugin).tag(config=False)
    extractor_plugin_inst = Instance(ExtractorPlugin).tag(config=False)

    @default("classes")
    def _classes_default(self):
        classes = super(ZipCollectApp, self)._classes_default()
        classes.append(ExtractorPlugin)
        classes.append(ZipCollectApp)
        classes.append(self.collector_plugin)
        return classes

    def _format_collect_path(self, collect_step, escape=False):
        kwargs = dict(
            downloaded=self.downloaded_directory,
            assignment_id=self.assignment_id,
            collect_step=collect_step,
        )

        if escape:
            base = re.escape(self.course_directory)
            split = full_split(self.collect_directory_structure)
            structure = [x.format(**kwargs) for x in split]
            path = re.escape(os.path.sep).join([base] + structure)
        else:
            path = os.path.join(
                self.course_directory,
                self.collect_directory_structure,
            ).format(**kwargs)

        return path

    def _mkdirs_if_missing(self, path):
        if not check_directory(path, write=True, execute=True):
            self.log.warn("Directory not found. Creating: {}".format(path))
            os.makedirs(path)

    def _clear_existing_files(self, path):
        if not os.listdir(path):
            return

        if self.force:
            self.log.warn("Clearing existing files in {}".format(path))
            rmtree(path)
            os.makedirs(path)
        else:
            self.fail(
                "Directory not empty: {}\nuse the --force option to clear "
                "previously existing files".format(path)
            )

    def _find_student(self, info):
        try:
            with open_gradebook(self.db_url) as gradebook:
                return gradebook.find_student(info.student_id)
        except MissingEntry:
            return None

    def get_timestamp(self):
        """Return the timestamp using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        return datetime.datetime.now(tz).strftime(self.timestamp_format)

    def extract_archive_files(self):
        """Extract archive (zip) files and submission files in the
        `archive_directory`. Files are extracted to the `extracted_directory`.
        Non-archive (zip) files found in the `archive_directory` are copied to
        the `extracted_directory`.
        """
        archive_path = self._format_collect_path(self.archive_directory)
        if not check_directory(archive_path, write=False, execute=True):
            self.log.warn("Directory not found: {}".format(archive_path))
            return

        extracted_path = self._format_collect_path(self.extracted_directory)
        self._mkdirs_if_missing(extracted_path)
        self._clear_existing_files(extracted_path)
        self.extractor_plugin_inst.extract(archive_path, extracted_path)

    def process_extracted_files(self):
        """Collect the files in the `extracted_directory` using a given plugin
        to process the filename of each file. Collected files are transfered to
        the students `submitted_directory`.
        """
        extracted_path = self._format_collect_path(self.extracted_directory)
        if not check_directory(extracted_path, write=False, execute=True):
            self.log.warn("Directory not found: {}".format(extracted_path))

        src_files = []
        for root, _, extracted_files in os.walk(extracted_path):
            for _file in extracted_files:
                src_files.append(os.path.join(root, _file))

        if not src_files:
            self.log.warning(
                "No files found in directory: {}".format(extracted_path))
            return

        src_files.sort()
        collected_data = self._collect_files(src_files)
        self._transfer_files(collected_data)

    def _collect_files(self, src_files):
        """Collect the files in the `extracted_directory` using a given plugin
        to process the filename of each file.

        Arguments
        ---------
        src_files: list
            List of all files in the `extracted_directory`

        Returns:
        --------
        Dict: Collected data object of the form
            {
                student_id: {
                    src_files: [src_file1, ...],
                    dest_files: [dest_file1, ...],
                    file_ids: [file_id1, ...],
                    timestamps: [timestamp1, ...],
                }, ...
            }
        """
        self.log.info("Start collecting files...")
        released_path = self._format_path(
            self.release_directory, '.', self.assignment_id)
        released_notebooks = find_all_notebooks(released_path)
        if not released_notebooks:
            self.log.warn(
                "No release notebooks found for assignment {}, did you forget "
                "to run 'nbgrader assign'?".format(self.assignment_id)
            )

        data = dict()
        invalid_files = 0
        processed_files = 0
        for _file in src_files:
            self.log.info("Processing file: {}".format(_file))
            info = self.collector_plugin_inst.collect(_file)
            if info is None or not isinstance(info, (CollectInfo, )):
                self.log.warn("Skipped. No match information provided.")
                invalid_files += 1
                continue

            info._validate(self)
            root, ext = os.path.splitext(_file)
            file_id = os.path.splitext(os.path.basename(info.file_id))[0]
            submission = '{}{}'.format(file_id, ext)
            if ext in ['.ipynb'] and submission not in released_notebooks:
                if self.strict:
                    self.log.warn("Skipped. Invalid notebook name.")
                    invalid_files += 1
                    continue
                self.log.warn("Invalid notebook name.")

            if self._find_student(info) is None:
                self.log.warn(
                    "Skipped. Student {} not found in gradebook."
                    "".format(info.student_id)
                )
                invalid_files += 1
                continue

            submitted_path = self._format_path(
                self.submitted_directory, info.student_id, self.assignment_id)
            dest_path = os.path.join(submitted_path, submission)

            timestamp = self.get_timestamp()
            if info.timestamp:
                try:
                    timestamp = parse_utc(info.timestamp)
                except ValueError:
                    self.log.warn(
                        "Could not parse the timestamp string. "
                        "Setting timestamp to the current time."
                    )

            if info.student_id in data.keys():
                if submission not in data[info.student_id]['file_ids']:
                    data[info.student_id]['file_ids'].append(submission)
                    data[info.student_id]['timestamps'].append(timestamp)
                    data[info.student_id]['src_files'].append(_file)
                    data[info.student_id]['dest_files'].append(dest_path)
                else:
                    ind = data[info.student_id]['file_ids'].index(submission)
                    old_timestamp = data[info.student_id]['timestamps'][ind]
                    if timestamp >= old_timestamp:
                        data[info.student_id]['timestamps'][ind] = timestamp
                        data[info.student_id]['src_files'][ind] = _file
                        data[info.student_id]['dest_files'][ind] = dest_path
                    else:
                        self.log.warn("Skipped. Older timestamp found.")
                        invalid_files += 1
            else:
                data[info.student_id] = dict(
                    file_ids=[submission],
                    timestamps=[timestamp],
                    src_files=[_file],
                    dest_files=[dest_path],
                )

            processed_files += 1

        if invalid_files > 0:
            self.log.warn(
                "{} files collected, {} files skipped"
                "".format(processed_files, invalid_files)
            )
        else:
            self.log.info("{} files collected".format(processed_files))
        return data

    def _transfer_files(self, collected_data):
        """Transfer collected files to the students `submitted_directory`.

        Arguments
        ---------
        collect: dict
            Collect data object of the form
                {
                    student_id: {
                        src_files: [src_file1, ...],
                        dest_files: [dest_file1, ...],
                        file_ids: [file_id1, ...],
                        timestamps: [timestamp1, ...],
                    }, ...
                }
        """
        if not collected_data:
            return

        self.log.info("Start transfering files...")
        for student_id, data in collected_data.items():
            dest_path = self._format_path(
                self.submitted_directory, student_id, self.assignment_id)
            self._mkdirs_if_missing(dest_path)
            self._clear_existing_files(dest_path)

            timestamp = max(data['timestamps'])
            for i in range(len(data['file_ids'])):
                src = data['src_files'][i]
                dest = data['dest_files'][i]
                self.log.info('Copying from: {}'.format(src))
                self.log.info('  Copying to: {}'.format(dest))
                shutil.copy(src, dest)

            dest = os.path.join(dest_path, 'timestamp.txt')
            self.log.info('Creating timestamp: {}'.format(dest))
            with open(dest, 'w') as fh:
                fh.write("{}".format(timestamp))

    def init_plugins(self):
        self.log.info(
            "Using file extractor: %s", self.extractor_plugin.__name__)
        self.extractor_plugin_inst = self.extractor_plugin(parent=self)

        self.log.info(
            "Using file collector: %s", self.collector_plugin.__name__)
        self.collector_plugin_inst = self.collector_plugin(parent=self)

    @catch_config_error
    def initialize(self, argv=None):
        cwd = os.getcwd()
        if cwd not in sys.path:
            # Add cwd to path so that custom plugins are found and loaded
            sys.path.insert(0, cwd)

        super(ZipCollectApp, self).initialize(argv)

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.assignment_id == "":
            self.fail(
                "Must provide assignment name:\n"
                "nbgrader zip_collect ASSIGNMENT"
            )

    def start(self):
        super(ZipCollectApp, self).start()
        self.init_plugins()
        self.extract_archive_files()
        self.process_extracted_files()
