import os

from IPython.nbconvert.exporters import HTMLExporter
from .assignmentexporter import AssignmentExporter

class FeedbackExporter(HTMLExporter, AssignmentExporter):

    def _template_path_default(self):
        return [os.path.join(os.path.dirname(__file__), "..", "html", "templates")]

    def _template_file_default(self):
        return 'feedback'
