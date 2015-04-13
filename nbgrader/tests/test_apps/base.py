import os

from IPython.nbformat import write as write_nb
from IPython.nbformat.v4 import new_notebook


class TestBase(object):

    @staticmethod
    def _empty_notebook(path):
        nb = new_notebook()
        with open(path, 'w') as f:
            write_nb(nb, f, 4)

    @staticmethod
    def _init_db():
        dbpath = "/tmp/nbgrader_test.db"
        if os.path.exists(dbpath):
            os.remove(dbpath)
        return "sqlite:///" + dbpath
