import warnings
from .generate_assignment import GenerateAssignment

class Assign(GenerateAssignment):

    def __init__(self, *args, **kwargs):
        super(Assign, self).__init__(*args, **kwargs)
        msg = (
            "The Assign class is now deprecated, please use GenerateAssignment "
            "instead. This class will be removed in a future version of "
            "nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
