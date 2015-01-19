from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags
from nbgrader.preprocessors import IncludeHeaderFooter, ClearSolutions, LockCells

aliases = {}
aliases.update(base_aliases)
aliases.update({
    'header': 'IncludeHeaderFooter.header',
    'footer': 'IncludeHeaderFooter.footer',
})

flags = {}
flags.update(base_flags)
flags.update({
})

examples = """
nbgrader assign master.ipynb --output=student.ipynb
nbgrader assign master/*.ipynb --build-directory=student

nbgrader assign --header=header.ipynb --footer=footer.ipynb
"""

class AssignApp(CustomNbConvertApp):

    name = Unicode(u'nbgrader-assign')
    description = Unicode(u'Prepare a student version of an assignment by removing solutions')
    aliases = aliases
    flags = flags
    examples = examples

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        classes = super(AssignApp, self)._classes_default()
        classes.extend([
            IncludeHeaderFooter,
            LockCells,
            ClearSolutions,
            ClearOutputPreprocessor
        ])
        return classes

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.IncludeHeaderFooter',
            'nbgrader.preprocessors.LockCells',
            'nbgrader.preprocessors.ClearSolutions',
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor'
        ]
        self.config.merge(self.extra_config)
