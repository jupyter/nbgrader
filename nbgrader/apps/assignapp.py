import sys
import shutil
import os

from textwrap import dedent

from IPython.utils.traitlets import List, Bool

from nbgrader.api import Gradebook, MissingEntry
from nbgrader.apps.baseapp import (
    BaseNbConvertApp, nbconvert_aliases, nbconvert_flags)
from nbgrader.preprocessors import (
    IncludeHeaderFooter,
    ClearSolutions,
    LockCells,
    ComputeChecksums,
    SaveCells,
    CheckCellMetadata,
    ClearOutput,
)

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'no-db': (
        {'SaveCells': {'enabled': False}},
        "Do not save information about grade cells into the database."
    ),
    'create': (
        {'AssignApp': {'create_assignment': True}},
        "Create an entry for the assignment in the database, if one does not already exist."
    ),
})

class AssignApp(BaseNbConvertApp):

    name = u'nbgrader-assign'
    description = u'Produce the version of an assignment to be released to students.'

    aliases = aliases
    flags = flags

    examples = """
        Produce the version of the assignment that is intended to be released to
        students. This performs several modifications to the original assignment:

            1. It inserts a header and/or footer to each notebook in the
               assignment, if the header/footer are specified.

            2. It locks certain cells so that they cannot be deleted by students
               accidentally (or on purpose!)

            3. It removes solutions from the notebooks and replaces them with
               code or text stubs saying (for example) "YOUR ANSWER HERE".

            4. It clears all outputs from the cells of the notebooks.

            5. It saves information about the cell contents so that we can warn
               students if they have changed the tests, or if they have failed
               to provide a response to a written answer. Specifically, this is
               done by computing a checksum of the cell contents and saving it
               into the cell metadata.

            6. It saves the tests used to grade students' code into a database,
               so that those tests can be replaced during autograding if they
               were modified by the student (you can prevent this by passing the
               --no-db flag).

               Additionally, the assignment must already be present in the
               database. To create it while running `nbgrader assign` if it
               doesn't already exist, pass the --create flag.

        `nbgrader assign` takes one argument (the name of the assignment), and
        looks for notebooks in the 'source' directory by default, according to
        the directory structure specified in `NbGraderConfig.directory_structure`.
        The student version is then saved into the 'release' directory.

        Note that the directory structure requires the `student_id` to be given;
        however, there is no student ID at this point in the process. Instead,
        `nbgrader assign` sets the student ID to be '.' so by default, files are
        read in according to:

            source/./{assignment_id}/{notebook_id}.ipynb

        and saved according to:

            release/./{assignment_id}/{notebook_id}.ipynb

        """

    create_assignment = Bool(
        False, config=True,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        )
    )

    @property
    def _input_directory(self):
        return self.source_directory

    @property
    def _output_directory(self):
        return self.release_directory

    export_format = 'notebook'

    preprocessors = List([
        IncludeHeaderFooter,
        LockCells,
        ClearSolutions,
        ClearOutput,
        CheckCellMetadata,
        ComputeChecksums,
        SaveCells
    ])

    def build_extra_config(self):
        extra_config = super(AssignApp, self).build_extra_config()
        extra_config.NbGraderConfig.student_id = '.'
        return extra_config

    def init_assignment(self, assignment_id, student_id):
        super(AssignApp, self).init_assignment(assignment_id, student_id)

        # try to get the assignment from the database, and throw an error if it
        # doesn't exist
        gb = Gradebook(self.db_url)
        try:
            gb.find_assignment(assignment_id)
        except MissingEntry:
            if self.create_assignment:
                self.log.warning("Creating assignment '%s'", assignment_id)
                gb.add_assignment(assignment_id)
            else:
                self.fail("No assignment called '%s' exists in the database", assignment_id)
