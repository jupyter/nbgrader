import os
import shutil
import pytest

from nbformat import write as write_nb
from nbformat.v4 import new_notebook


@pytest.mark.usefixtures("temp_cwd")
class BaseTestApp(object):

    def _empty_notebook(self, path):
        nb = new_notebook()
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'w') as f:
            write_nb(nb, f, 4)

    def _copy_file(self, src, dest):
        full_src = os.path.join(os.path.dirname(__file__), src)
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        shutil.copy(full_src, dest)

    def _make_file(self, path, contents=""):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        if os.path.exists(path):
            os.remove(path)
        with open(path, "w") as fh:
            fh.write(contents)

    def _get_permissions(self, filename):
        return oct(os.stat(filename).st_mode)[-3:]

    def _file_contents(self, path):
        with open(path, "r") as fh:
            contents = fh.read()
        return contents
