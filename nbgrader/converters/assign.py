import warnings
from .generate_assignment import GenerateAssignment

class Assign(GenerateAssignment):

    def __init__(self, *args, **kwargs):
        msg = (
            "`nbgrader assign` is now deprecated, please use `nbgrader "
            "generate_assignment` instead. This command will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg)
        super(Assign, self).__init__(*args, **kwargs)
