from textwrap import dedent

from IPython.utils.traitlets import Unicode, Dict, List
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor

from nbgrader.apps.baseapp import (
    BaseNbConvertApp, nbconvert_aliases, nbconvert_flags)
from nbgrader.preprocessors import (
    IncludeHeaderFooter,
    ClearSolutions,
    LockCells,
    ComputeChecksums,
    SaveCells,
    CheckCellMetadata
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
        {'SaveCells': {'create_assignment': True}},
        "Create the assignment at runtime if it does not exist."
    )
})

class AssignApp(BaseNbConvertApp):

    name = Unicode(u'nbgrader-assign')
    description = Unicode(u'Produce the version of an assignment to be released to students.')

    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        Produce the version of the assignment that is intended to be released to
        students. This performs several modifications to the original assignment:

            1. It inserts a header and/or footer to each notebook in the
               assignment, if the header/footer are specified.

            2. It locks certain cells so that they cannot be deleted by students
               accidentally (or on purpose!)

            3. It removes solutions from the notebooks and replaces them with
               code or text stubs saying (for example) "YOUR ANSWER HERE".

            4. It clears all outputs from the cells of the notebooks.

            5. It computes checksums of the cells that contain tests for the
               students' solutions, or that contain students' written answers.
               This is done so that we can warn students if they have changed
               the tests, or if they have failed to provide a response to a
               written answer.

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
    ))

    nbgrader_step_input = Unicode("source", config=True)
    nbgrader_step_output = Unicode("release", config=True)

    export_format = 'notebook'

    preprocessors = List([
        IncludeHeaderFooter,
        LockCells,
        ClearSolutions,
        ClearOutputPreprocessor,
        CheckCellMetadata,
        ComputeChecksums,
        SaveCells
    ])

    def build_extra_config(self):
        extra_config = super(AssignApp, self).build_extra_config()
        extra_config.NbGraderConfig.student_id = '.'
        return extra_config
