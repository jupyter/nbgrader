# coding: utf-8

import sys

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..converters import BaseConverter, GenerateSolution, NbGraderException
from traitlets.traitlets import MetaHasTraits
from typing import List, Any
from traitlets.config.loader import Config

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
    'force': (
        {'BaseConverter': {'force': True}},
        "Overwrite the solution if it already exists."
    ),
    'f': (
        {'BaseConverter': {'force': True}},
        "Overwrite the solution if it already exists."
    ),
})


class GenerateSolutionApp(NbGrader):

    name = u'nbgrader-generate-solution'
    description = u'Produce the solution of an assignment to be released to students.'

    aliases = aliases
    flags = flags

    examples = """
        Produce the solution of the assignment that is intended to be released to
        students. This essentially cleans up the assignment and runs all the cells providing
        the solution conceived by the instructor.

        `nbgrader generate_solution` takes one argument (the name of the assignment), and
        looks for notebooks in the 'source' directory by default, according to
        the directory structure specified in `CourseDirectory.directory_structure`.
        The student version is then saved into the 'solution' directory.

        Note that the directory structure requires the `student_id` to be given;
        however, there is no student ID also at this point in the process. Instead,
        `nbgrader generate_solution` sets the student ID to be '.' so by default, files are
        read in according to:

            source/./{assignment_id}/{notebook_id}.ipynb

        and saved according to:

            solution/./{assignment_id}/{notebook_id}.ipynb

        """

    @default("classes")
    def _classes_default(self) -> List[MetaHasTraits]:
        classes = super(GenerateSolutionApp, self)._classes_default()
        classes.extend([BaseConverter, GenerateSolution])
        return classes

    def start(self) -> None:
        super().start()

        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.coursedir.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]

        converter = GenerateSolution(coursedir=self.coursedir, parent=self)
        try:
            converter.start()
        except NbGraderException:
            sys.exit(1)
