from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Bool, Dict, List
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor

from nbgrader.apps.baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from nbgrader.preprocessors import SaveAutoGrades, Execute, OverwriteCells, SaveCells

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'no-overwrite': (
        {'OverwriteCells': {'enabled': False}},
        "Do not overwrite grade cells from the database."
    ),
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
        Running `nbgrader autograde` on a file by itself will produce a student
        version of that file in the same directory. In this case, it will produce
        "Problem 1.nbconvert.ipynb" (note that you need to specify the assignment
        name and the student id):
        
        > nbgrader autograde "Problem 1.ipynb" --assignment="Problem Set 1" --student=student1

        If you want to override the .nbconvert part of the filename, you can use
        the --output flag:

        > nbgrader autograde "Problem 1.ipynb" --output "Problem 1.graded.ipynb" --assignment="Problem Set 1" --student=student1

        Or, you can put the graded version in a different directory. In the
        following example, there will be a file "graded/Problem 1.ipynb" after
        running `nbgrader autograde`:

        > nbgrader autograde "Problem 1.ipynb" --build-dir=graded --assignment="Problem Set 1" --student=student1

        You can also use shell globs, and copy files from one directory to another:

        > nbgrader autograde submitted/*.ipynb --build-dir=graded --assignment="Problem Set 1" --student=student1

        If you want to overwrite grade cells with the source and metadata that
        was stored in the database when running `nbgrader assign` with --save-cells,
        you can use the --overwrite-cells flag:

        > nbgrader autograde "Problem 1.ipynb" --assignment="Problem Set 1" --student=student1 --overwrite-cells

        """
    ))

    nbgrader_step_input = Unicode("submitted")
    nbgrader_step_output = Unicode("autograded")

    preprocessors = List([
        ClearOutputPreprocessor,
        OverwriteCells,
        SaveCells,
        Execute,
        SaveAutoGrades
    ])

    def _classes_default(self):
        classes = super(AutogradeApp, self)._classes_default()
        for pp in self.preprocessors:
            if len(pp.class_traits(config=True)) > 0:
                classes.append(pp)
        return classes

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.default_preprocessors = self.preprocessors
        self.config.merge(self.extra_config)
