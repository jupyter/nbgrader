import os
from IPython.nbformat.reader import read as read_nb
from IPython.nbformat.v4 import new_code_cell, new_markdown_cell


class TestBase(object):

    def setup(self):
        self.pth = os.path.split(os.path.realpath(__file__))[0]
        with open(os.path.join(self.pth, "files/test.ipynb"), "r") as fh:
            self.nb = read_nb(fh)
        self.cells = self.nb.cells

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
