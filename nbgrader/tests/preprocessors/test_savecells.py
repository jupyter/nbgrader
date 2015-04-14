import pytest

from IPython.nbformat.v4 import new_notebook

from nbgrader.preprocessors import SaveCells
from nbgrader.api import Gradebook
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import (
    create_grade_cell, create_solution_cell, create_grade_and_solution_cell)


@pytest.fixture
def preprocessor():
    return SaveCells()


@pytest.fixture
def gradebook(db):
    gb = Gradebook(db)
    gb.add_assignment("ps0")
    return gb


@pytest.fixture
def resources(db, gradebook):
    return {
        "nbgrader": {
            "db_url": db,
            "assignment": "ps0",
            "notebook": "test",
        }
    }


class TestSaveCells(BaseTestPreprocessor):

    def test_save_code_grade_cell(self, preprocessor, resources):
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "code"

    def test_save_markdown_grade_cell(self, preprocessor, resources):
        cell = create_grade_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "markdown"

    def test_save_code_solution_cell(self, preprocessor, resources):
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "code"

    def test_save_markdown_solution_cell(self, preprocessor, resources):
        cell = create_solution_cell("hello", "markdown")
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "markdown"

    def test_save_code_grade_and_solution_cell(self, preprocessor, resources):
        cell = create_grade_and_solution_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "code"

        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "code"

    def test_save_markdown_grade_and_solution_cell(self, preprocessor, resources):
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.source == "hello"
        assert grade_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert grade_cell.cell_type == "markdown"

        solution_cell = gb.find_solution_cell(0, "test", "ps0")
        assert solution_cell.source == "hello"
        assert solution_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert solution_cell.cell_type == "markdown"
