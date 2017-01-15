import os
import re
import shutil
import datetime

from dateutil.tz import gettz
from textwrap import dedent
from traitlets import Bool, Instance, List, Type, Unicode
from traitlets.config.application import catch_config_error

from .baseapp import NbGrader

from ..api import open_gradebook, MissingEntry
from ..plugins import BasePlugin, FileNameProcessor
from ..plugins.zipcollect import CollectInfo
from ..utils import check_directory, full_split, rmtree, unzip


aliases = {
    'force': 'ZipCollectApp.force',
    'processor': 'ZipCollectApp.plugin_class',
    'update-db': 'ZipCollectApp.auto_update_database',
}
flags = {}


class ZipCollectApp(NbGrader):

    name = u'nbgrader-zip-collect'
    description = u''.join([
        'Collect assignment submissions from files and/or ',
        'archives (zip files) manually downloaded from a LMS.',
    ])

    aliases = aliases
    flags = flags

    examples = """
        TODO
        """

    force = Bool(
        default_value=False,
        help="TODO"
    ).tag(config=True)

    auto_update_database = Bool(
        default_value=True,
        help="TODO"
    ).tag(config=True)

    collect_directory_structure = Unicode(
        os.path.join(
            "{downloaded}", "{assignment_id}", "{collect_step}"),
        help=dedent(
            """
            TODO
            """
        )
    ).tag(config=True)

    downloaded_directory = Unicode(
        'downloaded',
        help=dedent(
            """
            TODO
            """
        )
    ).tag(config=True)

    archive_directory = Unicode(
        'archive',
        help=dedent(
            """
            TODO
            """
        )
    ).tag(config=True)

    extracted_directory = Unicode(
        'extracted',
        help=dedent(
            """
            TODO
            """
        )
    ).tag(config=True)

    invalid_directory = Unicode(
        'invalid',
        help=dedent(
            """
            TODO
            """
        )
    ).tag(config=True)

    zip_ext = List(
        ['.zip', '.gz'],
        help="TODO"
    ).tag(config=True)

    timezone = Unicode(
        "UTC",
        help="Timezone for recording timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z",
        help="Format string for timestamps"
    ).tag(config=True)

    plugin_class = Type(
        FileNameProcessor,
        klass=BasePlugin,
        help="TODO"
    ).tag(config=True)

    plugin_inst = Instance(BasePlugin).tag(config=False)

    def _classes_default(self):
        classes = super(ZipCollectApp, self)._classes_default()
        classes.append(ZipCollectApp)
        classes.append(self.plugin_class)
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
            self.log.info("Directory not found. Creating: {}".format(path))
            os.makedirs(path)

    def _clear_existing_files(self, path):
        if not os.listdir(path):
            return

        if self.force:
            self.log.info("Clearing existing files in {}".format(path))
            rmtree(path)
            os.makedirs(path)
        else:
            self.fail(
                "Directory not empty: {}\nuse the --force option to clear "
                "previously existing files".format(path)
            )

    def _create_or_update_student(self, info):
        if not self.auto_update_database:
            try:
                with open_gradebook(self.db_url) as gradebook:
                    return gradebook.find_student(info.student_id)
            except MissingEntry:
                return None

        else:
            kwargs = dict()
            for key in ['student_id', 'first_name', 'last_name', 'email']:
                value = getattr(info, key)
                if value is not None:
                    kwargs.update({key: value})

            with open_gradebook(self.db_url) as gradebook:
                return gradebook.update_or_create_student(info.student_id, **kwargs)

    def get_timestamp(self):
        """Set the timestap using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        return datetime.datetime.now(tz).strftime(self.timestamp_format)

    def process_archive_files(self):
        archive_path = self._format_collect_path(self.archive_directory)
        if not check_directory(archive_path, write=False, execute=True):
            self.fail("Directory not found: {}".format(archive_path))

        archive_files = [os.path.abspath(x) for x in os.listdir(archive_path)]
        if not archive_files:
            self.log.warning(
                "No files found in directory: {}".format(archive_path))
            return

        extract_to = self._format_collect_path(self.extracted_directory)
        self._mkdirs_if_missing(extract_to)
        self._clear_existing_files(extract_to)

        number_of_files = 0
        for zfile in archive_files:
            if os.path.isdir(zfile):
                self.log.warn("Sub-directory not processed: {}".format(zfile))
                continue

            root, ext = os.path.splitext(zfile)
            if ext.lower() in self.zip_ext:
                self.log.info("Extracting file: {}".format(zfile))
                success, nfiles, msg = unzip(zfile, extract_to, self.zip_ext)
                if not success:
                    self.fail(msg)
            else:
                nfiles = 1
                dest = os.path.join(extract_to, os.path.basename(zfile))
                self.log.info("Copying non-archive file to: {}".format(dest))
                shutil.copy(zfile, dest)

            number_of_files += nfiles

        # Sanity check
        extracted_file_count = len(os.listdir(extract_to))
        if number_of_files != extracted_file_count:
            self.log.warn(
                "File count mismatch. Processed or extracted {} files, but "
                "only found {} files in {}\nThis is due to the archive (zip) "
                "file/s either containing duplicates or sub-directories"
                "".format(number_of_files, extracted_file_count, extract_to)
            )

    def process_extracted_files(self):
        src_path = self._format_collect_path(self.extracted_directory)
        if not check_directory(src_path, write=False, execute=True):
            self.fail("Directory not found: {}".format(src_path))

        src_files = [os.path.abspath(x) for x in os.listdir(src_path)]
        if not src_files:
            self.log.warning("No files found in directory: {}".format(src_path))
            return

        processed_files = 0
        invalid_files = 0

        for _file in src_files:
            info = self.plugin_inst.collect(_file)
            if info is None or not isinstance(info, CollectInfo):
                self.log.warn(
                    "No CollectInfo provided for submitted "
                    "file. Skipping: {}".format(_file)
                )
                invalid_files += 1
                continue

            info._validate(self)
            student = self._create_or_update_student(info)
            if student is None:
                self.log.warn(
                    "Student {} not found in gradebook, for submitted "
                    "file. Skipping: {}".format(info.student_id, _file)
                )
                invalid_files += 1
                continue

            dest_path = self._format_path(
                self.submitted_directory,
                info.student_id,
                self.assignment_id
            )
            self._mkdirs_if_missing(dest_path)
            self._clear_existing_files(dest_path)

            root, ext = os.path.splitext(_file)
            notebook_id = os.path.splitext(os.path.basename(info.notebook_id))[0]
            dest = os.path.join(dest_path, notebook_id, ext.lower())
            self.log.info("Copying submission to: {}".format(dest))
            shutil.copy(_file, dest)

            dest = os.path.join(dest_path, 'timestamp.txt')
            timestamp = info.timestamp or self.get_timestamp()
            self.log.info("Creating timestamp file: {}".format(timestamp))
            with open(dest, 'r') as fh:
                fh.write(timestamp)

            processed_files += 1

        if invalid_files > 0:
            self.log.warn(
                "{} files processed, {} files skipped"
                "".format(processed_files, invalid_files)
            )
        else:
            self.log.info(
                "{} files processed".format(processed_files, invalid_files))

    def init_plugin(self):
        self.log.info("Using file processor: %s", self.plugin_class.__name__)
        self.plugin_inst = self.plugin_class(parent=self)

    @catch_config_error
    def initialize(self, argv=None):
        super(ZipCollectApp, self).initialize(argv)

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.assignment_id == "":
            self.fail(
                "Must provide assignment name:\n"
                "nbgrader zip_collect ASSIGNMENT [ --course COURSE ]"
            )

        self.init_plugin()

    def start(self):
        super(ZipCollectApp, self).start()
        self.process_archive_files()
        self.process_extracted_files()
