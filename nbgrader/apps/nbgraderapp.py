#!/usr/bin/env python
# encoding: utf-8

from textwrap import dedent

from IPython.utils.traitlets import Unicode
from nbgrader.apps import BaseNbGraderApp
from nbgrader import preprocessors


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
            'nbgrader.apps.assignapp.AssignApp',
            "Create a students version of a notebook"
        ),
        autograde=(
            'nbgrader.apps.autogradeapp.AutogradeApp',
            "Autograde a notebook by running it"
        ),
        formgrade=(
            'nbgrader.apps.formgradeapp.FormgradeApp',
            "Grade a notebook using an HTML form"
        ),
        feedback=(
            'nbgrader.apps.feedbackapp.FeedbackApp',
            "Generate feedback"
        ),
        validate=(
            'nbgrader.apps.validateapp.ValidateApp',
            "Validate a notebook"
        ),
        submit=(
            'nbgrader.apps.submitapp.SubmitApp',
            "Submit a completed assignment"
        ),
    )

    def _classes_default(self):
        classes = super(NbGraderApp, self)._classes_default()
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
