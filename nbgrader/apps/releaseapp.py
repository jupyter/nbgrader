# coding: utf-8

import warnings
from traitlets.config.application import catch_config_error
from .releaseassignmentapp import ReleaseAssignmentApp


class ReleaseApp(ReleaseAssignmentApp):

    @catch_config_error
    def initialize(self, argv=None):
        super(ReleaseApp, self).initialize(argv=argv)
        msg = (
            "`nbgrader release` is now deprecated, please use `nbgrader "
            "release_assignment` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
