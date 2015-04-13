import os
import glob
import tempfile
import shutil

from IPython.nbformat import current_nbformat
from IPython.nbformat import read as read_nb


class TestBase(object):

    pth = os.path.split(os.path.realpath(__file__))[0]
    files = {os.path.basename(x): x for x in glob.glob(os.path.join(pth, "files/*.ipynb"))}

    def setup(self):
        self.tempdir = None
        self.nbs = {}
        for basename, filename in self.files.items():
            with open(filename, "r") as fh:
                self.nbs[basename] = read_nb(fh, as_version=current_nbformat)

    def teardown(self):
        if self.tempdir and os.path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)

    def _init_db(self):
        self.tempdir = tempfile.mkdtemp()
        db_url = "sqlite:///" + os.path.join(self.tempdir, "nbgrader_test.db")
        return db_url
