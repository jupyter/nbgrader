import os

from IPython.nbformat import current_nbformat
from IPython.nbformat import read as read_nb


class BaseTestPreprocessor(object):

    def _read_nb(self, filename):
        fullpath = os.path.join(os.path.dirname(__file__), filename)
        with open(fullpath, "r") as fh:
            nb = read_nb(fh, as_version=current_nbformat)
        return nb
