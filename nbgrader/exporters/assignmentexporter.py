"""AssignmentExporter class"""

import os

from IPython.nbconvert.exporters import NotebookExporter
from IPython.nbconvert.exporters.exporter import ResourcesDict


class AssignmentExporter(NotebookExporter):
    """Exports to an IPython notebook assignment."""

    def from_filename(self, filename, resources=None, **kw):
        if resources is None:
            resources = ResourcesDict()
        if not 'metadata' in resources or resources['metadata'] == '':
            resources['metadata'] = ResourcesDict()

        path = os.path.split(filename)[0]
        resources['metadata']['path'] = path

        output, resources = super(AssignmentExporter, self).from_filename(
            filename, resources=resources, **kw)

        return output, resources
