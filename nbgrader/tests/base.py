import os
import glob

from IPython.nbformat import current_nbformat
from IPython.nbformat import read as read_nb
from IPython.nbformat import write as write_nb
from IPython.nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from nbgrader.utils import compute_checksum


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
    def _create_grade_cell(source, cell_type, grade_id, points):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["grade"] = True
        cell.metadata.nbgrader["grade_id"] = grade_id
        cell.metadata.nbgrader["points"] = points
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell

    @staticmethod
    def _create_solution_cell(source, cell_type):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["solution"] = True
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell

    @staticmethod
    def _create_grade_and_solution_cell(source, cell_type, grade_id, points):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["solution"] = True
        cell.metadata.nbgrader["grade"] = True
        cell.metadata.nbgrader["grade_id"] = grade_id
        cell.metadata.nbgrader["points"] = points
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell

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
