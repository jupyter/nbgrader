import os
import shutil
from abc import ABC

from traitlets import Bool

from .exchange import Exchange
from nbgrader.utils import check_mode


class ExchangeFetchAssignment(Exchange, ABC):

    replace_missing_files = Bool(False, help="Whether to replace missing files on fetch").tag(config=True)

    def copy_if_missing(self, src, dest, ignore=None):
        pass

