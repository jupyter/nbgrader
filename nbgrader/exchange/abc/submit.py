from textwrap import dedent
from traitlets import Bool

from .exchange import Exchange


class ExchangeSubmit(Exchange):

    strict = Bool(
        False,
        help=dedent(
            "Whether or not to submit the assignment if there are missing "
            "notebooks from the released assignment notebooks."
        )
    ).tag(config=True)

    add_random_string = Bool(
        True,
        help=dedent(
            "Whether to add a random string on the end of the submission."
        )
    ).tag(config=True)

    def init_release(self):
        pass

    def check_filename_diff(self):
        pass

