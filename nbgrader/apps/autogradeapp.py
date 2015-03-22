from textwrap import dedent

from IPython.utils.traitlets import Unicode, Dict, List
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor

from nbgrader.apps.baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from nbgrader.preprocessors import SaveAutoGrades, Execute, OverwriteCells

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'create': (
        {'SaveAutoGrades': {'create_student': True}},
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

    nbgrader_step_input = Unicode("submitted", config=True)
    nbgrader_step_output = Unicode("autograded", config=True)

    export_format = 'notebook'

    preprocessors = List([
        ClearOutputPreprocessor,
        OverwriteCells,
        Execute,
        SaveAutoGrades
    ])
