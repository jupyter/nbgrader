#!/usr/bin/env python
# encoding: utf-8

from textwrap import dedent
from traitlets import default, Unicode

from . import NbGrader
from ..api import Gradebook

aliases = {
    'log-level': 'Application.log_level',
    'course-dir': 'NbGrader.course_directory',
    'db': 'NbGrader.db_url'
}
flags = {}

student_add_aliases = {}
student_add_aliases.update(aliases)
student_add_aliases.update({
    'last-name': 'DbStudentAddApp.last_name',
    'first-name': 'DbStudentAddApp.first_name',
    'email': 'DbStudentAddApp.email'
})

class DbStudentAddApp(NbGrader):

    name = 'nbgrader-db-student-add'
    description = 'Add a student to the nbgrader database'

    aliases = student_add_aliases
    flags = flags

    last_name = Unicode(
        None,
        allow_none=True,
        help="The last name of the student (only for use with --add)"
    ).tag(config=True)

    first_name = Unicode(
        None,
        allow_none=True,
        help="The first name of the student (only for use with --add)"
    ).tag(config=True)

    email = Unicode(
        None,
        allow_none=True,
        help="The last name of the student (only for use with --add)"
    ).tag(config=True)

    def start(self):
        super(DbStudentAddApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No student id provided.")

        student_id = self.extra_args[0]
        student = {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "email": self.email
        }

        self.log.info("Creating/updating student with ID '%s': %s", student_id, student)
        gb = Gradebook(self.db_url)
        gb.update_or_create_student(student_id, **student)
        gb.close()


class DbStudentRemoveApp(NbGrader):

    name = 'nbgrader-db-student-remove'
    description = 'Remove a student from the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbStudentRemoveApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No student id provided.")

        student_id = self.extra_args[0]

        self.log.info("Removing student with ID '%s'", student_id)
        gb = Gradebook(self.db_url)
        gb.remove_student(student_id)
        gb.close()


class DbStudentImportApp(NbGrader):

    name = 'nbgrader-db-student-import'
    description = 'Import students into the nbgrader database from a CSV file'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbStudentImportApp, self).start()
        raise NotImplementedError


class DbStudentListApp(NbGrader):

    name = 'nbgrader-db-student-list'
    description = 'List students in the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbStudentListApp, self).start()

        gb = Gradebook(self.db_url)
        self.log.info("There are %d students in the database:", len(gb.students))
        for student in gb.students:
            self.log.info("%s (%s, %s) -- %s", student.id, student.last_name, student.first_name, student.email)
        gb.close()


assignment_add_aliases = {}
assignment_add_aliases.update(aliases)
assignment_add_aliases.update({
    'duedate': 'DbAssignmentAddApp.duedate',
})

class DbAssignmentAddApp(NbGrader):

    name = 'nbgrader-db-assignment-add'
    description = 'Add an assignment to the nbgrader database'

    aliases = assignment_add_aliases
    flags = flags

    duedate = Unicode(
        None,
        allow_none=True,
        help="The due date of the assignment (only for use with --add)"
    ).tag(config=True)

    def start(self):
        super(DbAssignmentAddApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No assignment id provided.")

        assignment_id = self.extra_args[0]
        assignment = {
            "duedate": self.duedate
        }

        self.log.info("Creating/updating assignment with ID '%s': %s", assignment_id, assignment)
        gb = Gradebook(self.db_url)
        gb.update_or_create_assignment(assignment_id, **assignment)
        gb.close()


class DbAssignmentRemoveApp(NbGrader):

    name = 'nbgrader-db-assignment-remove'
    description = 'Remove an assignment from the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbAssignmentRemoveApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No assignment id provided.")

        assignment_id = self.extra_args[0]

        self.log.info("Removing assignment with ID '%s'", assignment_id)
        gb = Gradebook(self.db_url)
        gb.remove_assignment(assignment_id)
        gb.close()


class DbAssignmentImportApp(NbGrader):

    name = 'nbgrader-db-assignment-import'
    description = 'Import assignments into the nbgrader database from a CSV file'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbAssignmentImportApp, self).start()
        raise NotImplementedError


class DbAssignmentListApp(NbGrader):

    name = 'nbgrader-db-assignment-list'
    description = 'List assignments int the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbAssignmentListApp, self).start()

        gb = Gradebook(self.db_url)
        self.log.info("There are %d assignments in the database:", len(gb.assignments))
        for assignment in gb.assignments:
            self.log.info("%s (due: %s)", assignment.name, assignment.duedate)
            for notebook in assignment.notebooks:
                self.log.info("    - %s", notebook.name)
        gb.close()


class DbStudentApp(NbGrader):

    name = 'nbgrader-db-student'
    description = u'Modify or list students in the nbgrader database'

    subcommands = {
        "add": (DbStudentAddApp, "Add a student to the database"),
        "remove": (DbStudentRemoveApp, "Remove a student from the database"),
        "list": (DbStudentListApp, "List students in the database"),
        "import": (DbStudentImportApp, "Import students into the database from a file")
    }

    @default("classes")
    def _classes_default(self):
        classes = super(DbStudentApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            self.fail("No db command given (run with --help for options)")

        # This starts subapps
        super(DbStudentApp, self).start()


class DbAssignmentApp(NbGrader):

    name = 'nbgrader-db-assignment'
    description = u'Modify or list assignments in the nbgrader database'

    subcommands = {
        "add": (DbAssignmentAddApp, "Add an assignment to the database"),
        "remove": (DbAssignmentRemoveApp, "Remove an assignment from the database"),
        "list": (DbAssignmentListApp, "List assignments in the database"),
        "import": (DbAssignmentImportApp, "Import assignments into the database from a file")
    }

    @default("classes")
    def _classes_default(self):
        classes = super(DbAssignmentApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            self.fail("No assignment command given (run with --help for options)")

        # This starts subapps
        super(DbAssignmentApp, self).start()


class DbApp(NbGrader):

    name = 'nbgrader-db'
    description = u'Perform operations on the nbgrader database'

    subcommands = dict(
        student=(
            DbStudentApp,
            dedent(
                """
                Add, remove, or list students in the nbgrader database.
                """
            ).strip()
        ),
        assignment=(
            DbAssignmentApp,
            dedent(
                """
                Add, remove, or list assignments in the nbgrader database.
                """
            ).strip()
        ),
    )

    @default("classes")
    def _classes_default(self):
        classes = super(DbApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            self.fail("No db command given (run with --help for options)")

        # This starts subapps
        super(DbApp, self).start()
