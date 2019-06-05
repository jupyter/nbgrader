# coding: utf-8

import warnings
from traitlets.config.application import catch_config_error
from .generatefeedbackapp import GenerateFeedbackApp


class FeedbackApp(GenerateFeedbackApp):

    @catch_config_error
    def initialize(self, argv=None):
        super(FeedbackApp, self).initialize(argv=argv)
        msg = (
            "`nbgrader feedback` is now deprecated, please use `nbgrader "
            "generate_feedback` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
