import warnings

from .release_assignment import ABCExchangeReleaseAssignment


class ABCExchangeRelease(ABCExchangeReleaseAssignment):

    def __init__(self, *args, **kwargs):
        super(ABCExchangeRelease, self).__init__(*args, **kwargs)
        msg = (
            "The ABCExchangeRelease class is now deprecated, please use "
            "ABCExchangeReleaseAssignment instead. This class will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
