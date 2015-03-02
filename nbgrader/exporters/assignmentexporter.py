"""AssignmentExporter class"""

import os
from textwrap import dedent

from IPython.utils.traitlets import Unicode, Integer
from IPython.nbconvert.exporters import NotebookExporter
from IPython.nbconvert.exporters.exporter import ResourcesDict


class AssignmentExporter(NotebookExporter):
    """Exports to an IPython notebook assignment."""

    assignment_id = Unicode(
        '', 
        config=True, 
        help="Assignment ID"
    )
    notebook_id = Unicode(
        '', 
        config=True, 
        help=dedent(
            """
            Notebook ID. If not specified, the name of the notebook (sans 
            extension) will be used.
            """
        )
    )
    student_id = Unicode(
        '', 
        config=True, 
        help="Student ID"
    )

    db_name = Unicode("gradebook", config=True, help="Database name")
    db_ip = Unicode("localhost", config=True, help="IP address for the database")
    db_port = Integer(27017, config=True, help="Port for the database")

    def from_filename(self, filename, resources=None, **kw):
        # construct the resources dictionary
        if resources is None:
            resources = ResourcesDict()
        if not 'metadata' in resources or resources['metadata'] == '':
            resources['metadata'] = ResourcesDict()
        if not 'nbgrader' in resources or resources['nbgrader'] == '':
            resources['nbgrader'] = ResourcesDict()

        # save information about the path
        path, basename = os.path.split(filename)
        notebook_name = basename[:basename.rfind('.')]
        resources['metadata']['name'] = notebook_name
        resources['metadata']['path'] = path

        # save information about the assignment and the student
        if self.notebook_id != '':
            resources['nbgrader']['notebook'] = self.notebook_id
        else:
            resources['nbgrader']['notebook'] = notebook_name
        if self.assignment_id != '':
            resources['nbgrader']['assignment'] = self.assignment_id
        if self.student_id != '':
            resources['nbgrader']['student'] = self.student_id

        # database stuff
        resources['nbgrader']['db_name'] = self.db_name
        resources['nbgrader']['db_ip'] = self.db_ip
        resources['nbgrader']['db_port'] = self.db_port

        output, resources = super(AssignmentExporter, self).from_filename(
            filename, resources=resources, **kw)

        return output, resources
