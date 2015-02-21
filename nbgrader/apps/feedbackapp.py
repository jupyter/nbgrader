from textwrap import dedent

from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, Dict
from IPython.nbconvert.writers import FilesWriter

from nbgrader.apps.baseapp import (
    BaseNbConvertApp, nbconvert_aliases, nbconvert_flags)
from nbgrader.preprocessors import FindStudentID, GetGrades
from nbgrader.exporters import FeedbackExporter

aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
    'assignment': 'AssignmentExporter.assignment_id',
    'student': 'AssignmentExporter.student_id',
    'db': 'AssignmentExporter.db_url',
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
    'overwrite-cells': (
        {'AutogradeApp': {'overwrite_cells': True}},
        "Overwrite grade cells from the database."
    )
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

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        classes = super(BaseNbConvertApp, self)._classes_default()
        classes.extend([
            FilesWriter,
            FeedbackExporter,
            FindStudentID,
            GetGrades
        ])
        return classes

    def _export_format_default(self):
        return 'feedback'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.FindStudentID',
            'nbgrader.preprocessors.GetGrades'
        ]
        self.config.merge(self.extra_config)
