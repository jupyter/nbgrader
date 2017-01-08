import os
import re
from textwrap import dedent

from traitlets import List, Bool, observe, default

from ..api import Gradebook, MissingEntry
from .baseapp import (
    BaseNbConvertApp, nbconvert_aliases, nbconvert_flags)
from ..preprocessors import (
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
del aliases['student']
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'no-db': (
        {
            'SaveCells': {'enabled': False},
            'AssignApp': {'no_database': True}
        },
        "Do not save information into the database."
    ),
    'no-metadata': (
        {
            'ClearSolutions': {'enforce_metadata': False},
            'CheckCellMetadata': {'enabled': False},
            'ComputeChecksums': {'enabled': False}
        },
        "Do not validate or modify cell metatadata."
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
        the directory structure specified in `NbGrader.directory_structure`.
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
        False,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        )
    ).tag(config=True)

    no_database = Bool(
        False,
        help=dedent(
            """
            Do not save information about the assignment into the database.
            """
        )
    ).tag(config=True)

    @default("permissions")
    def _permissions_default(self):
        return 644

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
        SaveCells,
        CheckCellMetadata
    ])

    def build_extra_config(self):
        extra_config = super(AssignApp, self).build_extra_config()
        extra_config.NbGrader.student_id = '.'
        extra_config.NbGrader.notebook_id = '*'
        return extra_config

    @observe("config")
    def _config_changed(self, change):
        if 'create_assignment' in change['new'].AssignApp:
            self.log.warn(
                "The AssignApp.create_assignment (or the --create flag) option is "
                "deprecated. Please specify your assignments through the "
                "`NbGrader.db_assignments` variable in your nbgrader config file."
            )
            del change['new'].AssignApp.create_assignment

        super(AssignApp, self)._config_changed(change)


    def _clean_old_notebooks(self, assignment_id, student_id):
        gb = Gradebook(self.db_url)
        assignment = gb.find_assignment(assignment_id)
        regexp = re.escape(os.path.sep).join([
            self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)", escape=True),
            "(?P<notebook_id>.*).ipynb"
        ])

        # find a set of notebook ids for new notebooks
        new_notebook_ids = set([])
        for notebook in self.notebooks:
            m = re.match(regexp, notebook)
            if m is None:
                raise RuntimeError("Could not match '%s' with regexp '%s'", notebook, regexp)
            gd = m.groupdict()
            if gd['assignment_id'] == assignment_id and gd['student_id'] == student_id:
                new_notebook_ids.add(gd['notebook_id'])

        # pull out the existing notebook ids
        old_notebook_ids = set(x.name for x in assignment.notebooks)

        # no added or removed notebooks, so nothing to do
        if old_notebook_ids == new_notebook_ids:
            gb.close()
            return

        # some notebooks have been removed, but there are submissions associated
        # with the assignment, so we don't want to overwrite stuff
        if len(assignment.submissions) > 0:
            gb.close()
            self.fail("Cannot modify existing assignment '%s' because there are submissions associated with it", assignment)

        # remove the old notebooks
        for notebook_id in (old_notebook_ids - new_notebook_ids):
            self.log.warning("Removing notebook '%s' from the gradebook", notebook_id)
            gb.remove_notebook(notebook_id, assignment_id)

        gb.close()

    def init_assignment(self, assignment_id, student_id):
        super(AssignApp, self).init_assignment(assignment_id, student_id)

        # try to get the assignment from the database, and throw an error if it
        # doesn't exist
        if not self.no_database:
            assignment = None
            for a in self.db_assignments:
                if a['name'] == assignment_id:
                    assignment = a.copy()
                    break

            if assignment is not None:
                del assignment['name']
                self.log.info("Updating/creating assignment '%s': %s", assignment_id, assignment)
                gb = Gradebook(self.db_url)
                gb.update_or_create_assignment(assignment_id, **assignment)
                gb.close()
            else:
                gb = Gradebook(self.db_url)
                try:
                    gb.find_assignment(assignment_id)
                except MissingEntry:
                    self.fail("No assignment called '%s' exists in the database", assignment_id)
                finally:
                    gb.close()

            # check if there are any extra notebooks in the db that are no longer
            # part of the assignment, and if so, remove them
            if self.notebook_id == "*":
                self._clean_old_notebooks(assignment_id, student_id)

