import warnings
from .fetch_assignment import ExchangeFetchAssignment

class ExchangeFetch(ExchangeFetchAssignment):

    def __init__(self, *args, **kwargs):
        super(ExchangeFetch, self).__init__(*args, **kwargs)
        msg = (
            "The ExchangeFetch class is now deprecated, please use "
            "ExchangeFetchAssignment instead. This class will be removed in a "
            "future version of nbgrader.")
        warnings.warn(msg, DeprecationWarning)
        self.log.warning(msg)
