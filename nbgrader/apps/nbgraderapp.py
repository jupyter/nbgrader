#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from textwrap import dedent

from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Bool

from nbgrader import preprocessors
from nbgrader.apps.baseapp import nbgrader_aliases, nbgrader_flags
from nbgrader.apps import (
    BaseNbGraderApp,
    AssignApp,
    AutogradeApp,
    FormgradeApp,
    FeedbackApp,
    ValidateApp,
    ReleaseApp,
    CollectApp,
    FetchApp,
    SubmitApp,
    ListApp,
    ExtensionApp
)

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'generate-config': (
        {'NbGraderApp' : {'generate_config': True}},
        "Generate a config file."
    ),
    'overwrite': (
        {'BasicConfig' : {'overwrite': True}},
        "Overwrite existing config files."
    ),
})


class NbGraderApp(BaseNbGraderApp):

    name = 'nbgrader'
    description = u'A system for assigning and grading notebooks'
    version = u'0.1'

    aliases = aliases
    flags = flags

    examples = """
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
        release=(
            ReleaseApp,
            dedent(
                """
                Release an assignment to students through the nbgrader exchange.
                Intended for use by instructors only.
                """
            ).strip()
        ),
        collect=(
            CollectApp,
            dedent(
                """
                Collect an assignment from students through the nbgrader exchange.
                Intended for use by instructors only.
                """
            ).strip()
        ),
        fetch=(
            FetchApp,
            dedent(
                """
                Fetch an assignment from an instructor through the nbgrader exchange.
                Intended for use by students only.
                """
            ).strip()
        ),
        submit=(
            SubmitApp,
            dedent(
                """
                Submit an assignment to an instructor through the nbgrader exchange.
                Intended for use by students only.
                """
            ).strip()
        ),
        list=(
            ListApp,
            dedent(
                """
                List inbound or outbound assignments in the nbgrader exchange.
                Intended for use by instructors and students.
                """
            ).strip()
        ),
        extension=(
            ExtensionApp,
            dedent(
                """
                Install and activate the "Create Assignment" notebook extension.
                """
            ).strip()
        )
    )

    generate_config = Bool(False, config=True, help="Generate a new config file")

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

    @catch_config_error
    def initialize(self, argv=None):
        super(NbGraderApp, self).initialize(argv)

    def start(self):
        # if we're generating a config file, then do only that
        if self.generate_config:
            s = self.generate_config_file()
            filename = "nbgrader_config.py"

            if os.path.exists(filename) and not self.overwrite:
                self.fail("Config file '{}' already exists (run with --overwrite to overwrite it)".format(filename))

            with open(filename, 'w') as fh:
                fh.write(s)
            self.log.info("New config file saved to '{}'".format(filename))
            sys.exit(0)

        # check: is there a subapp given?
        if self.subapp is None:
            self.print_help()
            sys.exit(1)

        # This starts subapps
        super(NbGraderApp, self).start()

def main():
    NbGraderApp.launch_instance()
