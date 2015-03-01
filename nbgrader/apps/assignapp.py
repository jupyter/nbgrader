from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List, Bool, Dict
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor
from IPython.nbconvert.writers import FilesWriter
from IPython.nbconvert.nbconvertapp import NbConvertApp

from nbgrader.apps.baseapp import BaseNbGraderApp, nbgrader_aliases, nbgrader_flags
from nbgrader.preprocessors import (
    IncludeHeaderFooter,
    ClearSolutions,
    LockCells,
    ComputeChecksums,
    SaveGradeCells,
    CheckGradeIds
)

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    'build-dir': 'FilesWriter.build_directory',
    'files': 'FilesWriter.files',
    'relpath': 'FilesWriter.relpath',
    'output': 'NbConvertApp.output_base',
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'save-cells': (
        {'AssignApp': {'save_cells': True}},
        "Save information about grade cells into the database."
    )
})

class AssignApp(BaseNbGraderApp, NbConvertApp):

    name = Unicode(u'nbgrader-assign')
    description = Unicode(u'Prepare a student version of an assignment by removing solutions')

    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        Running `nbgrader assign` on a file by itself will produce a student
        version of that file in the same directory. In this case, it will produce
        "Problem 1.nbconvert.ipynb":
        
        > nbgrader assign "Problem 1.ipynb"

        If you want to override the .nbconvert part of the filename, you can use
        the --output flag:

        > nbgrader assign "Problem 1.ipynb" --output "Problem 1.student.ipynb"

        Or, you can put the student version in a different directory. In the
        following example, there will be a file "student/Problem 1.ipynb" after
        running `nbgrader assign`:

        > nbgrader assign "Problem 1.ipynb" --build-dir=student

        You can also use shell globs, and copy files from one directory to another:

        > nbgrader assign teacher/*.ipynb --build-dir=student

        If you need to copy dependent files over as well, you can do this with
        the --files and --relpath flags. In the following example, all the .jpg
        files in the teacher/images/ folder will be linked to the student/images/
        folder (without the --relpath flag, they would be in student/teacher/images/):

        > nbgrader assign teacher/*.ipynb --build-dir=student --files='["teacher/images/*.jpg"]' --relpath=teacher

        """
    ))

    save_cells = Bool(False, config=True, help="Save information about grade cells into the database.")

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        classes = super(AssignApp, self)._classes_default()
        classes.extend([
            FilesWriter,
            IncludeHeaderFooter,
            CheckGradeIds,
            LockCells,
            ClearSolutions,
            ClearOutputPreprocessor,
            ComputeChecksums,
            SaveGradeCells
        ])
        return classes

    def _export_format_default(self):
        return 'assignment'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.IncludeHeaderFooter',
            'nbgrader.preprocessors.CheckGradeIds',
            'nbgrader.preprocessors.LockCells',
            'nbgrader.preprocessors.ClearSolutions',
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'nbgrader.preprocessors.ComputeChecksums'
        ]
        if self.save_cells:
            self.extra_config.Exporter.preprocessors.append(
                'nbgrader.preprocessors.SaveGradeCells'
            )
        self.config.merge(self.extra_config)
