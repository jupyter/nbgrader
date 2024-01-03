import warnings

from .fetch_assignment import ABCExchangeFetchAssignment


class ABCExchangeFetch(ABCExchangeFetchAssignment):

    def __init__(self, *args, **kwargs):
        super(ABCExchangeFetch, self).__init__(*args, **kwargs)
        msg = (
            "The ABCExchangeFetch class is now deprecated, please use "
            "ABCExchangeFetchAssignment instead. This class will be removed in a "
            "future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
