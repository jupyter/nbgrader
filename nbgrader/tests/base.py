import os
from IPython.nbformat.current import read as read_nb
from IPython.nbformat.current import new_code_cell, new_text_cell


class TestBase(object):

    def setup(self):
        self.pth = os.path.split(os.path.realpath(__file__))[0]
        with open(os.path.join(self.pth, "files/test.ipynb"), "r") as fh:
            self.nb = read_nb(fh, 'ipynb')
        self.cells = self.nb.worksheets[0].cells

    @staticmethod
    def _create_code_cell():
        source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
        cell = new_code_cell(input=source)
        return cell

    @staticmethod
    def _create_text_cell():
        source = "this is the answer!\n"
        cell = new_text_cell('markdown', source=source)
        return cell
