from traitlets import Bool

from .exchange import ABCExchange


class ABCExchangeReleaseAssignment(ABCExchange):

    force = Bool(False, help="Force overwrite existing files in the exchange.").tag(config=True)
