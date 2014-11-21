from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor, ExecutePreprocessor
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags
from nbgrader.preprocessors import FindStudentID, DisplayAutoGrades

aliases = {}
aliases.update(base_aliases)
aliases.update({
})

flags = {}
flags.update(base_flags)
flags.update({
})

examples = """
nbgrader validate "Problem 1.ipynb"
nbgrader validate "Problem Set 1/*.ipynb"
"""

class ValidateApp(CustomNbConvertApp):

    name = Unicode(u'nbgrader-validate')
    description = Unicode(u'Validate a notebook by running it')
    aliases = aliases
    flags = flags
    examples = examples
    log_level = 50
    output_dir = "/tmp"

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        classes = super(ValidateApp, self)._classes_default()
        classes.extend([
            ExecutePreprocessor,
            ClearOutputPreprocessor,
            DisplayAutoGrades
        ])
        return classes

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'IPython.nbconvert.preprocessors.ExecutePreprocessor',
            'nbgrader.preprocessors.DisplayAutoGrades'
        ]
        self.config.merge(self.extra_config)
