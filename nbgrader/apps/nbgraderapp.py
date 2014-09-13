#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

from IPython.utils.traitlets import Unicode, Bool, List
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.config.application import catch_config_error

_examples = """
nbgrader --help
nbgrader --help-all
nbgrader --NBGraderApp.overwrite=True

nbgrader --log-level=DEBUG
"""

class NBGraderApp(BaseIPythonApplication):

    name = Unicode('nbgrader')
    description = Unicode(u'A system for assigning and grading notebooks')
    version = Unicode(u'0.1')
    examples = Unicode(_examples)

    # The classes added here determine how configuration will be documented
    classes = List()
    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [
            ProfileDir
        ]

    @catch_config_error
    def initialize(self, argv=None):
        super(NBGraderApp,self).initialize(argv)
        self.stage_default_config_file()
    
    def start(self):
        # This starts subapps
        super(NBGraderApp,self).start()
        print("HI THERE!!!")

def main():
    NBGraderApp.launch_instance()
