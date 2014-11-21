import os
import glob
import subprocess as sp
from IPython.nbformat import current_nbformat
from IPython.nbformat import read as read_nb
from IPython.nbformat.v4 import new_code_cell, new_markdown_cell


class TestBase(object):

    pth = os.path.split(os.path.realpath(__file__))[0]
    files = {os.path.basename(x): x for x in glob.glob(os.path.join(pth, "files/*.ipynb"))}

    def setup(self):
        self.nbs = {}
        for basename, filename in self.files.items():
            with open(filename, "r") as fh:
                self.nbs[basename] = read_nb(fh, as_version=current_nbformat)

    @staticmethod
    def _create_code_cell():
        source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
        cell = new_code_cell(source=source)
        return cell

    @staticmethod
    def _create_text_cell():
        source = "this is the answer!\n"
        cell = new_markdown_cell(source=source)
        return cell

    @staticmethod
    def _run_command(command):
        proc = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
        if proc.wait() != 0:
            output = proc.communicate()[0]
            print(output.decode())
            raise AssertionError("process returned a non-zero exit code")
