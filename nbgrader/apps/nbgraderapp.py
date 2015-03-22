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
        nbgrader --help
        nbgrader --help-all
        nbgrader --log-level=DEBUG
        """
    ))

    subcommands = dict(
        assign=(
            AssignApp,
            "Create a students version of a notebook"
        ),
        autograde=(
            AutogradeApp,
            "Autograde a notebook by running it"
        ),
        formgrade=(
            FormgradeApp,
            "Grade a notebook using an HTML form"
        ),
        feedback=(
            FeedbackApp,
            "Generate feedback"
        ),
        validate=(
            ValidateApp,
            "Validate a notebook"
        ),
        submit=(
            SubmitApp,
            "Submit a completed assignment"
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
