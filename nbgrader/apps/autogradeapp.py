import sys

from textwrap import dedent

from IPython.utils.traitlets import Unicode, Dict, List, Bool

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
        "Create the student at runtime if they do not exist in the db."
    )
})

class AutogradeApp(BaseNbConvertApp):

    name = Unicode(u'nbgrader-autograde')
    description = Unicode(u'Autograde a notebook by running it')
    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        Autograde submitted assignments. This takes one 

        """
    ))

    create_student = Bool(
        False, config=True,
        help=dedent(
            """
            Whether to create the student at runtime if it does not
            already exist.
            """
        )
    )

    nbgrader_step_input = Unicode("submitted", config=True)
    nbgrader_step_output = Unicode("autograded", config=True)

    export_format = 'notebook'

    preprocessors = List([
        ClearOutput,
        OverwriteCells,
        Execute,
        SaveAutoGrades
    ])

    def init_single_notebook_resources(self, notebook_filename):
        resources = super(AutogradeApp, self).init_single_notebook_resources(notebook_filename)

        # try to get the student from the database, and throw an error if it
        # doesn't exist
        db_url = resources['nbgrader']['db_url']
        student_id = resources['nbgrader']['student']
        gb = Gradebook(db_url)
        try:
            gb.find_student(student_id)
        except MissingEntry:
            if self.create_student:
                self.log.warning("Creating student with ID '%s'", student_id)
                gb.add_student(student_id)
            else:
                self.log.error("No student with ID '%s' exists in the database", student_id)
                sys.exit(1)

        return resources
