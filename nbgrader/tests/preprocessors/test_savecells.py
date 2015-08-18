import pytest

from nbformat.v4 import new_notebook

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

    def test_save_new_cell(self, preprocessor, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        assert len(notebook.grade_cells) == 1
        assert len(notebook.solution_cells) == 1
        assert len(notebook.source_cells) == 1

        nb.cells.append(cell2)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb.db.refresh(notebook)
        assert len(notebook.grade_cells) == 2
        assert len(notebook.solution_cells) == 2
        assert len(notebook.source_cells) == 2

    def test_save_new_cell_with_submissions(self, preprocessor, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        assert len(notebook.grade_cells) == 1
        assert len(notebook.solution_cells) == 1
        assert len(notebook.source_cells) == 1

        gb.add_student("hacker123")
        gb.add_submission("ps0", "hacker123")
        nb.cells.append(cell2)

        with pytest.raises(RuntimeError):
            nb, resources = preprocessor.preprocess(nb, resources)

    def test_remove_cell(self, preprocessor, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb.cells.append(cell2)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        assert len(notebook.grade_cells) == 2
        assert len(notebook.solution_cells) == 2
        assert len(notebook.source_cells) == 2

        nb.cells = nb.cells[:-1]
        nb, resources = preprocessor.preprocess(nb, resources)

        gb.db.refresh(notebook)
        assert len(notebook.grade_cells) == 1
        assert len(notebook.solution_cells) == 1
        assert len(notebook.source_cells) == 1

    def test_remove_cell_with_submissions(self, preprocessor, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb.cells.append(cell2)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        assert len(notebook.grade_cells) == 2
        assert len(notebook.solution_cells) == 2
        assert len(notebook.source_cells) == 2

        gb.add_student("hacker123")
        gb.add_submission("ps0", "hacker123")
        nb.cells = nb.cells[:-1]

        with pytest.raises(RuntimeError):
            nb, resources = preprocessor.preprocess(nb, resources)

    def test_modify_cell(self, preprocessor, resources):
        nb = new_notebook()
        nb.cells.append(create_grade_and_solution_cell("hello", "markdown", "foo", 2))
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        solution_cell = gb.find_solution_cell("foo", "test", "ps0")
        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 2
        assert source_cell.source == "hello"

        nb.cells[-1] = create_grade_and_solution_cell("goodbye", "markdown", "foo", 1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb.db.refresh(notebook)
        gb.db.refresh(grade_cell)
        gb.db.refresh(solution_cell)
        gb.db.refresh(source_cell)
        assert grade_cell.max_score == 1
        assert source_cell.source == "goodbye"

    def test_modify_cell_with_submissions(self, preprocessor, resources):
        nb = new_notebook()
        nb.cells.append(create_grade_and_solution_cell("hello", "markdown", "foo", 2))
        nb, resources = preprocessor.preprocess(nb, resources)

        gb = preprocessor.gradebook
        notebook = gb.find_notebook("test", "ps0")
        grade_cell = gb.find_grade_cell("foo", "test", "ps0")
        solution_cell = gb.find_solution_cell("foo", "test", "ps0")
        source_cell = gb.find_source_cell("foo", "test", "ps0")
        assert grade_cell.max_score == 2
        assert source_cell.source == "hello"

        gb.add_student("hacker123")
        submission = gb.add_submission("ps0", "hacker123").notebooks[0]
        assert len(notebook.submissions) == 1

        nb.cells[-1] = create_grade_and_solution_cell("goodbye", "markdown", "foo", 1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gb.db.refresh(notebook)
        gb.db.refresh(submission)
        gb.db.refresh(grade_cell)
        gb.db.refresh(solution_cell)
        gb.db.refresh(source_cell)
        assert len(notebook.submissions) == 1
        assert grade_cell.max_score == 1
        assert source_cell.source == "goodbye"
