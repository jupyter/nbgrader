from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List
from IPython.nbconvert.writers import FilesWriter
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor, ExecutePreprocessor
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags
from nbgrader.preprocessors import FindStudentID, SaveAutoGrades

aliases = {}
aliases.update(base_aliases)
aliases.update({
    'student-id': 'AutogradeApp.student_id',
    'regexp': 'FindStudentID.regexp',
    'assignment': 'SaveAutoGrades.assignment_id',
    'build-directory': 'FilesWriter.build_directory',
    'output': 'NbConvertApp.output_base'
})

flags = {}
flags.update(base_flags)
flags.update({
})

examples = """
nbgrader autograde assignment.ipynb
nbgrader autograde assignment.ipynb --output=graded.ipynb
nbgrader autograde submitted/*.ipynb --build-directory=autograded
"""

class AutogradeApp(CustomNbConvertApp):

    name = Unicode(u'nbgrader-autograde')
    description = Unicode(u'Autograde a notebook by running it')
    aliases = aliases
    flags = flags
    examples = examples

    student_id = Unicode(u'', config=True)

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        classes = super(AutogradeApp, self)._classes_default()
        classes.extend([
            FindStudentID,
            ClearOutputPreprocessor,
            ExecutePreprocessor,
            SaveAutoGrades,
            FilesWriter
        ])
        return classes

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.FindStudentID',
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'IPython.nbconvert.preprocessors.ExecutePreprocessor',
            'nbgrader.preprocessors.SaveAutoGrades'
        ]
        self.config.merge(self.extra_config)
