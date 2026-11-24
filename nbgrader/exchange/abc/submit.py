from textwrap import dedent
from traitlets import Bool

from .exchange import ABCExchange


class ABCExchangeSubmit(ABCExchange):

    strict = Bool(
        False,
        help=dedent(
            "Whether or not to submit the assignment if there are missing "
            "notebooks from the released assignment notebooks."
        )
    ).tag(config=True)

