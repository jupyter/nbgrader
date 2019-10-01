import warnings

from nbgrader import exchange
from .release_assignment import ExchangeReleaseAssignment


class ExchangeRelease(ExchangeReleaseAssignment, exchange.ExchangeRelease):

    def __init__(self, *args, **kwargs):
        super(ExchangeRelease, self).__init__(*args, **kwargs)
        msg = (
            "The ExchangeRelease class is now deprecated, please use "
            "ExchangeReleaseAssignment instead. This class will be removed in "
            "a future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
