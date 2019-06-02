# coding: utf-8

import warnings
from .generateassignmentapp import GenerateAssignmentApp


class AssignApp(GenerateAssignmentApp):

    def __init__(self, *args, **kwargs):
        msg = (
            "`nbgrader assign` is now deprecated, please use `nbgrader "
            "generate_assignment` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg)
        super(AssignApp, self).__init__(*args, **kwargs)
