# coding: utf-8

import sys

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..converters import BaseConverter, InstantiateTests, NbGraderException
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
    'no-db': (
        {
            'InstantiateTests': {'no_database': True}
        },
        "Do not save information into the database."
    ),
    'no-metadata': (
        {
            'InstantiateTests': {'enforce_metadata': False},
        },
        "Do not validate or modify cell metatadata."
    ),
    'create': (
        {'InstantiateTests': {'create_assignment': True}},
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


class InstantiateTestsApp(NbGrader):

    name = u'nbgrader-instantiate-tests'
    description = u'Produce the version of an assignment to be released to students.'

    aliases = aliases
    flags = flags

    examples = """
        Produce a version of the assignment that includes generated test code based on the
        autotest directives in the notebook. This "instantiated" version is still editable by instructors
        and still contains all solutions. The instantiated notebook does not limit test cell heights to
        enable instructors to easily see all test code. The instantiated notebook
        is useful for instructors to examine/debug the test code that autotest will
        generate in the release version. Students will not receive this version of the notebook.
        The instantiate tests app performs several modifications to the original assignment:

            1. It clears all outputs from the cells of the notebooks.

            2. It produces a version of the source notebook with all autotests instantiated
               in the instantiated notebooks folder (by default, 'instantiated/').

               If the assignment is not already present in the database, it
               will be automatically created when running `nbgrader instantiate_tests`.

        `nbgrader instantiate_tests` takes one argument (the name of the assignment), and
        looks for notebooks in the 'source' directory by default, according to
        the directory structure specified in `CourseDirectory.directory_structure`.
        The instantiated version is then saved into the 'instantiated' directory.

        Note that the directory structure requires the `student_id` to be given;
        however, there is no student ID at this point in the process. Instead,
        `nbgrader instantiate_tests` sets the student ID to be '.' so by default, files are
        read in according to:

            source/./{assignment_id}/{notebook_id}.ipynb

        and saved according to:

            instantiated/./{assignment_id}/{notebook_id}.ipynb

        """

    @default("classes")
    def _classes_default(self) -> List[MetaHasTraits]:
        classes = super(InstantiateTestsApp, self)._classes_default()
        classes.extend([BaseConverter, InstantiateTests])
        return classes

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super()._load_config(cfg, **kwargs)

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

        converter = InstantiateTests(coursedir=self.coursedir, parent=self)
        try:
            converter.start()
        except NbGraderException:
            sys.exit(1)
