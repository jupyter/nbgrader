import os

from traitlets import List
from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor

from .baseapp import BaseNbConvertApp, nbconvert_aliases, nbconvert_flags
from ..preprocessors import GetGrades

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
})

class FeedbackApp(BaseNbConvertApp):

    name = u'nbgrader-feedback'
    description = u'Generate feedback from a graded notebook'

    aliases = aliases
    flags = flags

    examples = """
        Create HTML feedback for students after all the grading is finished.
        This takes a single parameter, which is the assignment ID, and then (by
        default) looks at the following directory structure:

            autograded/*/{assignment_id}/*.ipynb

        from which it generates feedback the the corresponding directories
        according to:

            feedback/{student_id}/{assignment_id}/{notebook_id}.html

        Running `nbgrader feedback` requires that `nbgrader autograde` (and most
        likely `nbgrader formgrade`) have been run and that all grading is
        complete.

        To generate feedback for all submissions for "Problem Set 1":
            nbgrader feedback "Problem Set 1"

        To generate feedback only for the student with ID 'Hacker':
            nbgrader feedback "Problem Set 1" --student Hacker

        To feedback for only the notebooks that start with '1':
            nbgrader feedback "Problem Set 1" --notebook "1*"
        """

    @property
    def _input_directory(self):
        return self.autograded_directory

    @property
    def _output_directory(self):
        return self.feedback_directory

    preprocessors = List([
        GetGrades,
        CSSHTMLHeaderPreprocessor
    ])

    def _classes_default(self):
        classes = super(FeedbackApp, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def _export_format_default(self):
        return 'html'

    def build_extra_config(self):
        extra_config = super(FeedbackApp, self).build_extra_config()

        if 'template_file' not in self.config.HTMLExporter:
            extra_config.HTMLExporter.template_file = 'feedback'
        if 'template_path' not in self.config.HTMLExporter:
            template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'formgrader', 'templates'))
            extra_config.HTMLExporter.template_path = ['.', template_path]

        return extra_config
