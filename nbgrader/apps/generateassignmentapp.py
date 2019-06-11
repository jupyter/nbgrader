# coding: utf-8

import sys

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..converters import BaseConverter, GenerateAssignment, NbGraderException

aliases = {
    'course': 'CourseDirectory.course_id'
}
aliases.update(nbgrader_aliases)
del aliases['student']
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'no-db': (
        {
            'SaveCells': {'enabled': False},
            'GenerateAssignment': {'no_database': True}
        },
        "Do not save information into the database."
    ),
    'no-metadata': (
        {
            'ClearSolutions': {'enforce_metadata': False},
            'ClearHiddenTests': {'enforce_metadata': False},
            'ClearMarkScheme': {'enforce_metadata': False},
            'CheckCellMetadata': {'enabled': False},
            'ComputeChecksums': {'enabled': False}
        },
        "Do not validate or modify cell metatadata."
    ),
    'create': (
        {'GenerateAssignment': {'create_assignment': True}},
        "Deprecated: Create an entry for the assignment in the database, if one does not already exist. "
        "This is now the default."
    ),
    'force': (
        {'BaseConverter': {'force': True}},
        "Overwrite an assignment/submission if it already exists."
    ),
    'f': (
        {'BaseConverter': {'force': True}},
        "Overwrite an assignment/submission if it already exists."
    ),
})


class GenerateAssignmentApp(NbGrader):

    name = u'nbgrader-generate-assignment'
    description = u'Produce the version of an assignment to be released to students.'

    aliases = aliases
    flags = flags

    examples = """
        Produce the version of the assignment that is intended to be released to
        students. This performs several modifications to the original assignment:

            1. It inserts a header and/or footer to each notebook in the
               assignment, if the header/footer are specified.

            2. It locks certain cells so that they cannot be deleted by students
               accidentally (or on purpose!)

            3. It removes solutions from the notebooks and replaces them with
               code or text stubs saying (for example) "YOUR ANSWER HERE".

            4. It clears all outputs from the cells of the notebooks.

            5. It saves information about the cell contents so that we can warn
               students if they have changed the tests, or if they have failed
               to provide a response to a written answer. Specifically, this is
               done by computing a checksum of the cell contents and saving it
               into the cell metadata.

            6. It saves the tests used to grade students' code into a database,
               so that those tests can be replaced during autograding if they
               were modified by the student (you can prevent this by passing the
               --no-db flag).

               If the assignment is not already present in the database, it
               will be automatically created when running `nbgrader generate_assignment`.

        `nbgrader generate_assignment` takes one argument (the name of the assignment), and
        looks for notebooks in the 'source' directory by default, according to
        the directory structure specified in `CourseDirectory.directory_structure`.
        The student version is then saved into the 'release' directory.

        Note that the directory structure requires the `student_id` to be given;
        however, there is no student ID at this point in the process. Instead,
        `nbgrader generate_assignment` sets the student ID to be '.' so by default, files are
        read in according to:

            source/./{assignment_id}/{notebook_id}.ipynb

        and saved according to:

            release/./{assignment_id}/{notebook_id}.ipynb

        """

    @default("classes")
    def _classes_default(self):
        classes = super(GenerateAssignmentApp, self)._classes_default()
        classes.extend([BaseConverter, GenerateAssignment])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'AssignApp' in cfg:
            self.log.warning(
                "Use GenerateAssignment in config, not AssignApp. Outdated config:\n%s",
                '\n'.join(
                    'AssignApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.AssignApp.items()
                )
            )
            cfg.GenerateAssignment.merge(cfg.AssignApp)
            del cfg.AssignApp

        super(GenerateAssignmentApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(GenerateAssignmentApp, self).start()

        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.coursedir.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]

        converter = GenerateAssignment(coursedir=self.coursedir, parent=self)
        try:
            converter.start()
        except NbGraderException:
            sys.exit(1)
