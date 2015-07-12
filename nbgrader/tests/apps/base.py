import os
import shutil
import pytest
import stat


from IPython.nbformat import write as write_nb
from IPython.nbformat.v4 import new_notebook


@pytest.mark.usefixtures("temp_cwd")
class BaseTestApp(object):

    def _empty_notebook(self, path):
        nb = new_notebook()
        full_dest = os.path.join(os.getcwd(), path)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        with open(full_dest, 'w') as f:
            write_nb(nb, f, 4)

    def _copy_file(self, src, dest):
        full_src = os.path.join(os.path.dirname(__file__), src)
        full_dest = os.path.join(os.getcwd(), dest)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        os.chmod(full_src, 0o666)
        shutil.copy(full_src, full_dest)

    def _make_file(self, path, contents=""):
        full_dest = os.path.join(os.getcwd(), path)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        with open(full_dest, "w") as fh:
            fh.write(contents)

    def _get_permissions(self, filename):
        return oct(os.stat(filename).st_mode)[-3:]
