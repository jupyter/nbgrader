from traitlets import Bool

from .exchange import Exchange


class ExchangeFetchAssignment(Exchange):

    replace_missing_files = Bool(False, help="Whether to replace missing files on fetch").tag(config=True)
