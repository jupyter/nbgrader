# coding: utf-8

import warnings
from traitlets.config.application import catch_config_error
from .generateassignmentapp import GenerateAssignmentApp


class AssignApp(GenerateAssignmentApp):

    @catch_config_error
    def initialize(self, argv=None):
        super(AssignApp, self).initialize(argv=argv)
        msg = (
            "`nbgrader assign` is now deprecated, please use `nbgrader "
            "generate_assignment` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
