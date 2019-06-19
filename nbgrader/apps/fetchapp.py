# coding: utf-8

import warnings
from traitlets.config.application import catch_config_error
from .fetchassignmentapp import FetchAssignmentApp


class FetchApp(FetchAssignmentApp):

    @catch_config_error
    def initialize(self, argv=None):
        super(FetchApp, self).initialize(argv=argv)
        msg = (
            "`nbgrader fetch` is now deprecated, please use `nbgrader "
            "fetch_assignment` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
