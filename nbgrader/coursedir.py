import os
import re

from textwrap import dedent

from traitlets.config import LoggingConfigurable
from traitlets import Integer, Bool, Unicode, List, default, validate, TraitError

from .utils import full_split, parse_utc


class CourseDirectory(LoggingConfigurable):

    course_id = Unicode(
        '',
        help=dedent(
            """
            A key that is unique per instructor and course. This can be
            specified, either by setting the config option, or using the
            --course option on the command line.
            """
        )
    ).tag(config=True)

    @validate('course_id')
    def _validate_course_id(self, proposal):
        if proposal['value'].strip() != proposal['value']:
            self.log.warning("course_id '%s' has trailing whitespace, stripping it away", proposal['value'])
        return proposal['value'].strip()

    student_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match student IDs. This can be changed to filter by
            student. Note: this is always changed to '.' when running `nbgrader
            assign`, as the assign step doesn't have any student ID associated
            with it. With `nbgrader submit`, this instead forces the use of
            an alternative student ID for the submission. See `nbgrader submit --help`.

            If the ID is purely numeric and you are passing it as a flag on the
            command line, you will need to escape the quotes in order to have
            it detected as a string, for example `--student="\"12345\""`. See:

                https://github.com/jupyter/nbgrader/issues/743

            for more details.
            """
        )
    ).tag(config=True)

    @validate('student_id')
    def _validate_student_id(self, proposal):
        if proposal['value'].strip() != proposal['value']:
            self.log.warning("student_id '%s' has trailing whitespace, stripping it away", proposal['value'])
        return proposal['value'].strip()

    student_id_exclude = Unicode(
        "",
        help=dedent(
            """
            Comma-separated list of student IDs to exclude.  Counterpart of student_id.

            This is useful when running commands on all students, but certain
            students cause errors or otherwise must be left out.  Works at
            least for autograde, generate_feedback, and release_feedback.
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

    @validate('assignment_id')
    def _validate_assignment_id(self, proposal):
        if '+' in proposal['value']:
            raise TraitError('Assignment names should not contain the following characters: +')
        if proposal['value'].strip() != proposal['value']:
            self.log.warning("assignment_id '%s' has trailing whitespace, stripping it away", proposal['value'])
        return proposal['value'].strip()

    notebook_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match notebook names, excluding the '.ipynb' extension.
            This can be changed to filter by notebook.
            """
        )
    ).tag(config=True)

    @validate('notebook_id')
    def _validate_notebook_id(self, proposal):
        if proposal['value'].strip() != proposal['value']:
            self.log.warning("notebook_id '%s' has trailing whitespace, stripping it away", proposal['value'])
        return proposal['value'].strip()

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

    db_url = Unicode(
        "",
        help=dedent(
            """
            URL to the database. Defaults to sqlite:///<root>/gradebook.db,
            where <root> is another configurable variable.
            """
        )
    ).tag(config=True)

    @default("db_url")
    def _db_url_default(self):
        return "sqlite:///{}".format(
            os.path.abspath(os.path.join(self.root, "gradebook.db")))

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

    root = Unicode(
        '',
        help=dedent(
            """
            The root directory for the course files (that includes the `source`,
            `release`, `submitted`, `autograded`, etc. directories). Defaults to
            the current working directory.
            """
        )
    ).tag(config=True)

    groupshared = Bool(
        False,
        help=dedent(
            """
            Make all instructor files group writeable (g+ws, default g+r only)
            and exchange directories group readable/writeable (g+rws, default
            g=nothing only ) by default.  This should only be used if you
            carefully set the primary groups of your notebook servers and fully
            understand the unix permission model.  This changes the default
            permissions from 444 (unwriteable) to 664 (writeable), so that
            other instructors are able to delete/overwrite files.
            """
        )
    ).tag(config=True)

    @default("root")
    def _root_default(self):
        return os.getcwd()

    @validate('root')
    def _validate_root(self, proposal):
        path = os.path.abspath(proposal['value'])
        if path != proposal['value']:
            self.log.warning("root '%s' is not absolute, standardizing it to '%s", proposal['value'], path)
        return path

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__",
            "feedback",
        ],
        help=dedent(
            """
            List of file names or file globs.
            Upon copying directories recursively, matching files and
            directories will be ignored with a debug message.
            """
        )
    ).tag(config=True)

    include = List(
        [
            "*",
        ],
        help=dedent(
            """
            List of file names or file globs.
            Upon copying directories recursively, non matching files
            will be ignored with a debug message.
            """
        )
    ).tag(config=True)

    max_file_size = Integer(
        100000,
        help=dedent(
            """
            Maximum size of files (in kilobytes; default: 100Mb).
            Upon copying directories recursively, larger files will be
            ignored with a warning.
            """
        )
    ).tag(config=True)

    def format_path(self, nbgrader_step, student_id, assignment_id, escape=False):
        kwargs = dict(
            nbgrader_step=nbgrader_step,
            student_id=student_id,
            assignment_id=assignment_id
        )

        if escape:
            base = re.escape(self.root)
            structure = [x.format(**kwargs) for x in full_split(self.directory_structure)]
            path = re.escape(os.path.sep).join([base] + structure)
        else:
            path = os.path.join(self.root, self.directory_structure).format(**kwargs)

        return path

    def get_existing_timestamp(self, dest_path):
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
