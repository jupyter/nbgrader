from nbgrader.preprocessors import SaveCells
from nbgrader.api import Gradebook
from IPython.nbformat.v4 import new_notebook

from .base import TestBase


class TestSaveCells(TestBase):

    def setup(self):
        super(TestSaveCells, self).setup()
        db_url = self._init_db()
        self.gb = Gradebook(db_url)
        self.gb.add_assignment("ps0")

        self.preprocessor = SaveCells()
        self.resources = {
            "nbgrader": {
                "db_url": db_url,
                "assignment": "ps0",
                "notebook": "test"
            }
        }

    def test_save_code_grade_cell(self):
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "code"

    def test_save_markdown_grade_cell(self):
        cell = self._create_grade_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "markdown"

    def test_save_code_solution_cell(self):
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "code"

    def test_save_markdown_solution_cell(self):
        cell = self._create_solution_cell("hello", "markdown")
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "markdown"

    def test_save_code_grade_and_solution_cell(self):
        cell = self._create_grade_and_solution_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "code"

        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "code"

    def test_save_markdown_grade_and_solution_cell(self):
        cell = self._create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = self.preprocessor.preprocess(nb, self.resources)

        gb = self.preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "markdown"

        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "markdown"
