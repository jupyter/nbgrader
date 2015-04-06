import os
import dateutil.parser

from textwrap import dedent

from IPython.utils.traitlets import List, Bool

from nbgrader.api import Gradebook, MissingEntry
from nbgrader.apps.baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from nbgrader.preprocessors import SaveAutoGrades, Execute, OverwriteCells, ClearOutput

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
    )
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

    @property
    def _input_directory(self):
        return self.submitted_directory

    @property
    def _output_directory(self):
        return self.autograded_directory

    export_format = 'notebook'

    preprocessors = List([
        ClearOutput,
        OverwriteCells,
        Execute,
        SaveAutoGrades
    ])

    def init_assignment(self, assignment_id, student_id):
        super(AutogradeApp, self).init_assignment(assignment_id, student_id)

        # try to get the student from the database, and throw an error if it
        # doesn't exist
        gb = Gradebook(self.db_url)
        try:
            gb.find_student(student_id)
        except MissingEntry:
            if self.create_student:
                self.log.warning("Creating student with ID '%s'", student_id)
                gb.add_student(student_id)
            else:
                self.fail("No student with ID '%s' exists in the database", student_id)

        # try to read in a timestamp from file
        src_path = self._format_source(assignment_id, student_id)
        timestamp = self._get_existing_timestamp(src_path)
        if timestamp:
            submission = gb.update_or_create_submission(
                assignment_id, student_id, timestamp=timestamp)
            self.log.info("%s submitted at %s", submission, timestamp)

            # if the submission is late, print out how many seconds late it is
            if timestamp and submission.total_seconds_late > 0:
                self.log.warning("%s is %s seconds late", submission, submission.total_seconds_late)
