import pytest

from IPython.nbformat.v4 import new_notebook

from nbgrader.preprocessors import SaveCells
from nbgrader.api import Gradebook
from nbgrader.utils import compute_checksum
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import (
    create_grade_cell, create_solution_cell, create_grade_and_solution_cell,
    create_locked_cell)


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
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "code"

        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert source_cell.locked

    def test_save_code_solution_cell(self, preprocessor, resources):
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        gb.find_solution_cell("foo", "test", "ps0")

        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert not source_cell.locked

    def test_save_markdown_solution_cell(self, preprocessor, resources):
        cell = create_solution_cell("hello", "markdown", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        gb.find_solution_cell("foo", "test", "ps0")

        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert not source_cell.locked

    def test_save_code_grade_and_solution_cell(self, preprocessor, resources):
        cell = create_grade_and_solution_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "code"

        gb.find_solution_cell("foo", "test", "ps0")

        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert not source_cell.locked

    def test_save_markdown_grade_and_solution_cell(self, preprocessor, resources):
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "markdown"

        gb.find_solution_cell("foo", "test", "ps0")

        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert not source_cell.locked

    def test_save_locked_code_cell(self, preprocessor, resources):
        cell = create_locked_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert source_cell.locked

    def test_save_locked_markdown_cell(self, preprocessor, resources):
        cell = create_locked_cell("hello", "markdown", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert source_cell.locked
