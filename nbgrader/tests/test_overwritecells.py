from nose.tools import assert_equal
from nbgrader.preprocessors import SaveCells, OverwriteCells
from nbgrader.api import Gradebook
from nbgrader.utils import compute_checksum
from IPython.nbformat.v4 import new_notebook

from .base import TestBase


class TestSaveCells(TestBase):

    def setup(self):
        super(TestSaveCells, self).setup()
        db_url = self._init_db()
        self.gb = Gradebook(db_url)
        self.gb.add_assignment("ps0")

        self.preprocessor1 = SaveCells()
        self.preprocessor2 = OverwriteCells()
        self.resources = {
            "nbgrader": {
                "db_url": db_url,
                "assignment": "ps0",
                "notebook": "test"
            }
        }

    def test_overwrite_points(self):
        """Are points overwritten for grade cells?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.metadata.nbgrader["points"] = 2
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.metadata.nbgrader["points"], 1)

    def test_overwrite_grade_source(self):
        """Is the source overwritten for grade cells?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.source = "hello!"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.source, "hello")

    def test_dont_overwrite_grade_and_solution_source(self):
        """Is the source not overwritten for grade+solution cells?"""
        cell = self._create_grade_and_solution_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.source = "hello!"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

    def test_dont_overwrite_solution_source(self):
        """Is the source not overwritten for solution cells?"""
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.source = "hello!"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.source, "hello!")

    def test_overwrite_grade_cell_type(self):
        """Is the cell type overwritten for grade cells?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.cell_type = "markdown"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.cell_type, "code")

    def test_overwrite_grade_cell_type(self):
        """Is the cell type overwritten for solution cells?"""
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.cell_type = "markdown"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.cell_type, "code")

    def test_overwrite_grade_checksum(self):
        """Is the checksum overwritten for grade cells?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.metadata.nbgrader["checksum"], compute_checksum(cell))

    def test_overwrite_solution_checksum(self):
        """Is the checksum overwritten for solution cells?"""
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = self.preprocessor1.preprocess(nb, self.resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = self.preprocessor2.preprocess(nb, self.resources)

        assert_equal(cell.metadata.nbgrader["checksum"], compute_checksum(cell))

