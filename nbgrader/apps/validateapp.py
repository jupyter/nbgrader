import tempfile
import shutil

from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Dict
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor
from nbgrader.preprocessors import DisplayAutoGrades, Execute
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
        You can run `nbgrader validate` on just a single file, e.g.:

        > nbgrader validate "Problem 1.ipynb"

        Or, you can run it on multiple files using shell globs:

        > nbgrader validate "Problem Set 1/*.ipynb"

        If you want to test instead that none of the tests pass (rather than that
        all of the tests pass, which is the default), you can use the --invert
        flag:

        > nbgrader validate --invert "Problem 1.ipynb"
        """
    ))

    def _log_level_default(self):
        return 50

    def _classes_default(self):
        classes = super(ValidateApp, self)._classes_default()
        classes.extend([
            ClearOutputPreprocessor,
            Execute,
            DisplayAutoGrades
        ])
        return classes

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'nbgrader.preprocessors.Execute',
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
