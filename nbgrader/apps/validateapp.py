import tempfile
import shutil

from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Dict
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor, ExecutePreprocessor
from nbgrader.preprocessors import DisplayAutoGrades
from nbgrader.apps.baseapp import BaseNbConvertApp, nbconvert_flags, nbconvert_aliases

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'invert': (
        {'DisplayAutoGrades': {'invert': True}},
        "Complain when cells pass, rather than vice versa."
    )
})

class ValidateApp(BaseNbConvertApp):

    name = Unicode(u'nbgrader-validate')
    description = Unicode(u'Validate a notebook by running it')
    
    aliases = Dict(aliases)
    flags = Dict(flags)
    
    examples = Unicode(dedent(
        """
        nbgrader validate "Problem 1.ipynb"
        nbgrader validate "Problem Set 1/*.ipynb"
        """
    ))

    def _log_level_default(self):
        return 50

    def _classes_default(self):
        classes = super(ValidateApp, self)._classes_default()
        classes.extend([
            ClearOutputPreprocessor,
            ExecutePreprocessor,
            DisplayAutoGrades
        ])
        return classes

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'IPython.nbconvert.preprocessors.ExecutePreprocessor',
            'nbgrader.preprocessors.DisplayAutoGrades'
        ]
        self.config.merge(self.extra_config)

    def convert_notebooks(self):
        self.tmpdir = tempfile.mkdtemp()
        self.writer.build_directory = self.tmpdir
        try:
            super(ValidateApp, self).convert_notebooks()
        finally:
            shutil.rmtree(self.tmpdir)
