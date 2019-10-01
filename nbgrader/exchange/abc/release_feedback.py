import os
import shutil
import glob
import re
from abc import ABC
from stat import S_IRUSR, S_IWUSR, S_IXUSR, S_IRGRP, S_IWGRP, S_IXGRP, S_IXOTH, S_ISGID

from .exchange import Exchange
from nbgrader.utils import notebook_hash, make_unique_key


class ExchangeReleaseFeedback(Exchange, ABC):
    pass