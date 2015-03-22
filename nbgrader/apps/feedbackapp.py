import os
from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Dict, List
from IPython.nbconvert.exporters import HTMLExporter

from nbgrader.apps.baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from nbgrader.preprocessors import GetGrades

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
})

class FeedbackApp(BaseNbConvertApp):

    name = Unicode(u'nbgrader-feedback')
    description = Unicode(u'Generate feedback from a graded notebook')
    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        nbgrader feedback student.ipynb --output student.ipynb
        """
    ))

    nbgrader_step_input = Unicode("autograded")
    nbgrader_step_output = Unicode("feedback")

    preprocessors = List([
        GetGrades
    ])

    def _classes_default(self):
        classes = super(FeedbackApp, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def _export_format_default(self):
        return 'html'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = self.preprocessors
    
        if 'template_file' not in self.config.HTMLExporter:
            self.extra_config.HTMLExporter.template_file = 'feedback'
        if 'template_path' not in self.config.HTMLExporter:
            template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../html/templates'))
            self.extra_config.HTMLExporter.template_path = ['.', template_path]

        self.config.merge(self.extra_config)
