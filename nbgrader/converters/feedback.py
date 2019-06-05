import warnings
from .generate_feedback import GenerateFeedback

class Feedback(GenerateFeedback):

    def __init__(self, *args, **kwargs):
        super(Feedback, self).__init__(*args, **kwargs)
        msg = (
            "The Feedback class is now deprecated, please use GenerateFeedback "
            "instead. This class will be removed in a future version of "
            "nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
