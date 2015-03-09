from IPython.nbconvert.exporters import HTMLExporter
from IPython import nbformat
from .assignmentexporter import AssignmentExporter

class FeedbackExporter(AssignmentExporter):

    def from_notebook_node(self, nb, resources=None, **kw):
        # this will return a notebook in string format, so we want to load
        # it back in as a notebook node and then pass it to the HTML exporter
        output, resources = super(FeedbackExporter, self).from_notebook_node(
            nb, resources=resources, **kw)

        exporter = HTMLExporter(config=self.config)
        output, resources = exporter.from_notebook_node(
            nbformat.reads(output, as_version=self.nbformat_version),
            resources=resources, **kw)

        return output, resources
