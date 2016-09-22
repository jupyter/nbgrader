import os
import shutil

from textwrap import dedent
from traitlets import List, Bool

from .baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from ..preprocessors import (
    AssignLatePenalties, ClearOutput, DeduplicateIds, OverwriteCells, SaveAutoGrades, Execute, LimitOutput)
from ..api import Gradebook, MissingEntry
from .. import utils

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'create': (
        {'AutogradeApp': {'create_student': True}},
        "Create an entry for the student in the database, if one does not already exist."
    ),
    'no-execute': (
        {
            'Execute': {'enabled': False},
            'ClearOutput': {'enabled': False}
        },
        "Don't execute notebooks and clear output when autograding."
    ),
})

class AutogradeApp(BaseNbConvertApp):

    name = u'nbgrader-autograde'
    description = u'Autograde a notebook by running it'

    aliases = aliases
    flags = flags

    examples = """
        Autograde submitted assignments. This takes one argument for the
        assignment id, and then (by default) autogrades assignments from the
        following directory structure:

            submitted/*/{assignment_id}/*.ipynb

        and saves the autograded files to the corresponding directory in:

            autograded/{student_id}/{assignment_id}/{notebook_id}.ipynb

        The student IDs must already exist in the database. If they do not, you
        can tell `nbgrader autograde` to add them on the fly by passing the
        --create flag.

        Note that the assignment must also be present in the database. If it is
        not, you should first create it using `nbgrader assign`. Then, during
        autograding, the cells that contain tests for the students' answers will
        be overwritten with the master version of the tests that is saved in the
        database (this prevents students from modifying the tests in order to
        improve their score).

        To grade all submissions for "Problem Set 1":

            nbgrader autograde "Problem Set 1"

        To grade only the submission by student with ID 'Hacker':

            nbgrader autograde "Problem Set 1" --student Hacker

        To grade only the notebooks that start with '1':

            nbgrader autograde "Problem Set 1" --notebook "1*"

        By default, student submissions are re-executed and their output cleared.
        For long running notebooks, it can be useful to disable this with the
        '--no-execute' flag:

            nbgrader autograde "Problem Set 1" --no-execute

        Note, however, that doing so will not guarantee that students' solutions
        are correct. If you use this flag, you should make sure you manually
        check all solutions. For example, if a student saved their notebook with
        all outputs cleared, then using --no-execute would result in them
        receiving full credit on all autograded problems.
        """

    create_student = Bool(
        False, config=True,
        help=dedent(
            """
            Whether to create the student at runtime if it does not
            already exist.
            """
        )
    )

    _sanitizing = True

    @property
    def _input_directory(self):
        if self._sanitizing:
            return self.submitted_directory
        else:
            return self.autograded_directory

    @property
    def _output_directory(self):
        return self.autograded_directory

    export_format = 'notebook'

    sanitize_preprocessors = List([
        ClearOutput,
        DeduplicateIds,
        OverwriteCells
    ])
    autograde_preprocessors = List([
        Execute,
        LimitOutput,
        SaveAutoGrades,
        AssignLatePenalties,
    ])

    preprocessors = List([])

    def _config_changed(self, name, old, new):
        if 'create_student' in new.AutogradeApp:
            self.log.warn(
                "The AutogradeApp.create_student (or the --create flag) option is "
                "deprecated. Please specify your assignments through the "
                "`NbGrader.db_students` variable in your nbgrader config file."
            )
            del new.AutogradeApp.create_student

        super(AutogradeApp, self)._config_changed(name, old, new)

    def init_assignment(self, assignment_id, student_id):
        super(AutogradeApp, self).init_assignment(assignment_id, student_id)

        # try to get the student from the database, and throw an error if it
        # doesn't exist
        student = None
        for s in self.db_students:
            if s['id'] == student_id:
                student = s.copy()
                break

        if student is not None:
            del student['id']
            self.log.info("Creating/updating student with ID '%s': %s", student_id, student)
            gb = Gradebook(self.db_url)
            gb.update_or_create_student(student_id, **student)
            gb.close()
        else:
            self.fail("No student with ID '%s' exists in the config", student_id)

        # try to read in a timestamp from file
        src_path = self._format_source(assignment_id, student_id)
        timestamp = self._get_existing_timestamp(src_path)
        gb = Gradebook(self.db_url)
        if timestamp:
            submission = gb.update_or_create_submission(
                assignment_id, student_id, timestamp=timestamp)
            self.log.info("%s submitted at %s", submission, timestamp)

            # if the submission is late, print out how many seconds late it is
            if timestamp and submission.total_seconds_late > 0:
                self.log.warning("%s is %s seconds late", submission, submission.total_seconds_late)
        else:
            submission = gb.update_or_create_submission(assignment_id, student_id)
        gb.close()

        # copy files over from the source directory
        self.log.info("Overwriting files with master versions from the source directory")
        dest_path = self._format_dest(assignment_id, student_id)
        source_path = self._format_path(self.source_directory, '.', assignment_id)
        source_files = utils.find_all_files(source_path, self.ignore + ["*.ipynb"])

        # copy them to the build directory
        for filename in source_files:
            dest = os.path.join(dest_path, os.path.relpath(filename, source_path))
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            if os.path.exists(dest):
                os.remove(dest)
            self.log.info("Copying %s -> %s", filename, dest)
            shutil.copy(filename, dest)

        # ignore notebooks that aren't in the database
        notebooks = []
        gb = Gradebook(self.db_url)
        for notebook in self.notebooks:
            notebook_id = os.path.splitext(os.path.basename(notebook))[0]
            try:
                gb.find_notebook(notebook_id, assignment_id)
            except MissingEntry:
                self.log.warning("Skipping unknown notebook: %s", notebook)
                continue
            else:
                notebooks.append(notebook)
        gb.close()
        self.notebooks = notebooks

    def _init_preprocessors(self):
        self.exporter._preprocessors = []
        if self._sanitizing:
            preprocessors = self.sanitize_preprocessors
        else:
            preprocessors = self.autograde_preprocessors

        for pp in preprocessors:
            self.exporter.register_preprocessor(pp)

    def convert_single_notebook(self, notebook_filename):
        self.log.info("Sanitizing %s", notebook_filename)
        self._sanitizing = True
        self._init_preprocessors()
        super(AutogradeApp, self).convert_single_notebook(notebook_filename)

        notebook_filename = os.path.join(self.writer.build_directory, os.path.basename(notebook_filename))
        self.log.info("Autograding %s", notebook_filename)
        self._sanitizing = False
        self._init_preprocessors()
        super(AutogradeApp, self).convert_single_notebook(notebook_filename)

        self._sanitizing = True
