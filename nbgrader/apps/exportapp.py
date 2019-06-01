# coding: utf-8

from traitlets import Type, Instance, default
from .baseapp import NbGrader
from ..plugins import ExportPlugin, CsvExportPlugin
from ..api import Gradebook

aliases = {
    'log-level' : 'Application.log_level',
    'db': 'CourseDirectory.db_url',
    'to' : 'ExportPlugin.to',
    'exporter': 'ExportApp.plugin_class',
    'assignment' : 'ExportPlugin.assignment',
    'student': 'ExportPlugin.student',
    'course': 'CourseDirectory.course_id'
}
flags = {}


class ExportApp(NbGrader):

    name = u'nbgrader-export'
    description = u'Export information from the database to another format.'

    aliases = aliases
    flags = flags

    examples = """

        The default is to export to a file called "grades.csv", i.e.:

            nbgrader export

        You can customize the filename with the --to flag:

            nbgrader export --to mygrades.csv

        You can export the grades for a single (or limited set) of students 
        or assignments with the --assignment and/or --student flag:

            nbgrader export --assignment [assignmentID] 
                            --student [studentID1,studentID2]

        Where the studentIDs and assignmentIDs are a list of IDs and 
        assignments. The assignments or studentIDs need to quoted if they 
        contain not only numbers. The square brackets are obligatory.

        To change the export type, you will need a class that inherits from
        nbgrader.plugins.ExportPlugin. If your exporter is named
        `MyCustomExporter` and is saved in the file `myexporter.py`, then:

            nbgrader export --exporter=myexporter.MyCustomExporter

        """

    plugin_class = Type(
        CsvExportPlugin,
        klass=ExportPlugin,
        help="The plugin class for exporting the grades."
    ).tag(config=True)

    plugin_inst = Instance(ExportPlugin).tag(config=False)

    def init_plugin(self):
        self.log.info("Using exporter: %s", self.plugin_class.__name__)
        self.plugin_inst = self.plugin_class(parent=self)

    @default("classes")
    def _classes_default(self):
        classes = super(ExportApp, self)._classes_default()
        classes.append(ExportApp)
        classes.append(ExportPlugin)
        return classes

    def start(self):
        super(ExportApp, self).start()
        self.init_plugin()
        with Gradebook(self.coursedir.db_url, self.coursedir.course_id) as gb:
            self.plugin_inst.export(gb)
