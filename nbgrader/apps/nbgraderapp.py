#!/usr/bin/env python
# coding: utf-8

import sys
import os

from textwrap import dedent

from traitlets import default
from traitlets.config.application import catch_config_error
from jupyter_core.application import NoStart

import nbgrader
from .baseapp import nbgrader_aliases, nbgrader_flags
from . import (
    NbGrader,
    AssignApp,
    GenerateAssignmentApp,
    AutogradeApp,
    FormgradeApp,
    FeedbackApp,
    ReleaseFeedbackApp,
    ValidateApp,
    ReleaseApp,
    CollectApp,
    FetchApp,
    FetchFeedbackApp,
    SubmitApp,
    ListApp,
    ExtensionApp,
    QuickStartApp,
    ExportApp,
    DbApp,
    UpdateApp,
    ZipCollectApp,
    GenerateConfigApp
)

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
})


class NbGraderApp(NbGrader):

    name = u'nbgrader'
    description = u'A system for assigning and grading notebooks'
    version = nbgrader.__version__

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
        configured through the `NbGrader` class (run `nbgrader --help-all`
        to see these options).

        For more details on how each of the subcommands work, please see the help
        for that command (e.g. `nbgrader generate_assignment --help-all`).
        """

    subcommands = dict(
        assign=(
            AssignApp,
            dedent(
                """
                DEPRECATED, please use generate_assignment instead.
                """
            ).strip()
        ),
        generate_assignment=(
            GenerateAssignmentApp,
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
        release_feedback=(
            ReleaseFeedbackApp,
            dedent(
                """
                Release assignment feedback to students through the nbgrader exchange.
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
        zip_collect=(
            ZipCollectApp,
            dedent(
                """
                Collect assignment submissions from files and/or archives (zip
                files) manually downloaded from a LMS.
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
        fetch_feedback=(
            FetchFeedbackApp,
            dedent(
                """
                Fetch feedback for an assignment from an instructor through the nbgrader exchange.
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
        ),
        quickstart=(
            QuickStartApp,
            dedent(
                """
                Create an example class files directory with an example
                config file and assignment.
                """
            ).strip()
        ),
        export=(
            ExportApp,
            dedent(
                """
                Export grades from the database to another format.
                """
            ).strip()
        ),
        db=(
            DbApp,
            dedent(
                """
                Perform operations on the nbgrader database, such as adding,
                removing, importing, and listing assignments or students.
                """
            ).strip()
        ),
        update=(
            UpdateApp,
            dedent(
                """
                Update nbgrader cell metadata to the most recent version.
                """
            ).strip()
        ),
        generate_config=(
            GenerateConfigApp,
            dedent(
                """
                Generates a default nbgrader_config.py file.
                """
            ).strip()
        ),
    )

    @default("classes")
    def _classes_default(self):
        return self.all_configurable_classes()

    @catch_config_error
    def initialize(self, argv=None):
        super(NbGraderApp, self).initialize(argv)

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            print("No command given (run with --help for options). List of subcommands:\n")
            self.print_subcommands()

        # This starts subapps
        super(NbGraderApp, self).start()

    def print_version(self):
        print("Python version {}".format(sys.version))
        print("nbgrader version {}".format(nbgrader.__version__))


def main():
    NbGraderApp.launch_instance()
