from traitlets import Bool

from .exchange import Exchange


class ExchangeReleaseAssignment(Exchange):

    force = Bool(False, help="Force overwrite existing files in the exchange.").tag(config=True)
