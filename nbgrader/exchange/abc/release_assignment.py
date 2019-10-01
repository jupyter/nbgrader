import os
import shutil
from abc import ABC
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISGID, ST_MODE
)

from traitlets import Bool

from .exchange import Exchange
from nbgrader.utils import self_owned


class ExchangeReleaseAssignment(Exchange, ABC):

    force = Bool(False, help="Force overwrite existing files in the exchange.").tag(config=True)
