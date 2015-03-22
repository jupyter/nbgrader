#!/usr/bin/env python
# encoding: utf-8

from textwrap import dedent

from IPython.utils.traitlets import Unicode
from nbgrader import preprocessors
from nbgrader.apps import (
    BaseNbGraderApp,
    AssignApp,
    AutogradeApp,
    FormgradeApp,
    FeedbackApp,
    ValidateApp,
    SubmitApp
)


class NbGraderApp(BaseNbGraderApp):

    name = Unicode('nbgrader')
    description = Unicode(u'A system for assigning and grading notebooks')
    version = Unicode(u'0.1')
    examples = Unicode(dedent(
        """
        The nbgrader application is a system for assigning and grading notebooks.
        Each subcommand of this program corresponds to a different step in the
        grading process. In order to facilitate the grading pipeline, nbgrader
        places some constraints on how the assignments must be structured. By
        default, the directory structure for the assignments must look like this:

            {nbgrader_step}/{student_id}/{assignment_id}/{notebook_id}.ipynb

        where 'nbgrader_step' is the step in the nbgrader pipeline, 'student_id'
        is the ID of the student, 'assignment_id' is the name of the assignment,
        and 'notebook_id' is the name of the notebook (excluding the extension).
        For example, when running `nbgrader autograde "Problem Set 1"`, the
        autograder will first look for all notebooks for all students in the
        following directories:

            submitted/*/Problem Set 1/*.ipynb

        and it will write the autograded notebooks to the corresponding directory
        and filename for each notebook and each student:

            autograded/{student_id}/Problem Set 1/{notebook_id}.ipynb

        These variables, as well as the overall directory structure, can be
        configured through the `NbGraderConfig` class (run `nbgrader --help-all`
        to see these options).

        For more details on how each of the subcommands work, please see the help
        for that command (e.g. `nbgrader assign --help-all`).
        """
    ))

    subcommands = dict(
        assign=(
            AssignApp,
            dedent(
                """
                Create the student version of an assignment. Intended for use by
                instructors only.
                """
            ).strip()
        ),
        autograde=(
            AutogradeApp,
            dedent(
                """
                Autograde submitted assignments. Intended for use by instructors
                only.
                """
            ).strip()
        ),
        formgrade=(
            FormgradeApp,
            dedent(
                """
                Manually grade assignments (after autograding). Intended for use
                by instructors only.
                """
            ).strip()
        ),
        feedback=(
            FeedbackApp,
            dedent(
                """
                Generate feedback (after autograding and manual grading).
                Intended for use by instructors only.
                """
            ).strip()
        ),
        validate=(
            ValidateApp,
            dedent(
                """
                Validate a notebook in an assignment. Intended for use by
                instructors and students.
                """
            ).strip()
        ),
        submit=(
            SubmitApp,
            "Submit an assignment. Intended for use by students only."
        ),
    )

    def _classes_default(self):
        classes = super(NbGraderApp, self)._classes_default()

        # include all the apps that have configurable options
        for appname, (app, help) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        # include all preprocessors that have configurable options
        for pp_name in preprocessors.__all__:
            pp = getattr(preprocessors, pp_name)
            if len(pp.class_traits(config=True)) > 0:
                classes.append(pp)

        return classes

    def start(self):
        # This starts subapps
        super(NbGraderApp, self).start()

def main():
    NbGraderApp.launch_instance()
