from traitlets import Bool

from .exchange import ABCExchange


class ABCExchangeFetchAssignment(ABCExchange):

    replace_missing_files = Bool(False, help="Whether to replace missing files on fetch").tag(config=True)
