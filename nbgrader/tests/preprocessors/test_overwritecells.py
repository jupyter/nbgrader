import pytest

from nbgrader.preprocessors import SaveCells, OverwriteCells
from nbgrader.api import Gradebook
from nbgrader.utils import compute_checksum
from IPython.nbformat.v4 import new_notebook

from .base import BaseTestPreprocessor
from .. import create_grade_cell, create_solution_cell, create_grade_and_solution_cell


@pytest.fixture
def preprocessors():
    return (SaveCells(), OverwriteCells())


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
            "notebook": "test"
        }
    }


class TestOverwriteCells(BaseTestPreprocessor):

    def test_overwrite_points(self, preprocessors, resources):
        """Are points overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["points"] = 2
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["points"] == 1

    def test_overwrite_grade_source(self, preprocessors, resources):
        """Is the source overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello"

    def test_dont_overwrite_grade_and_solution_source(self, preprocessors, resources):
        """Is the source not overwritten for grade+solution cells?"""
        cell = create_grade_and_solution_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello!"

    def test_dont_overwrite_solution_source(self, preprocessors, resources):
        """Is the source not overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello!"

    def test_overwrite_grade_cell_type(self, preprocessors, resources):
        """Is the cell type overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.cell_type = "markdown"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.cell_type == "code"

    def test_overwrite_solution_cell_type(self, preprocessors, resources):
        """Is the cell type overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.cell_type = "markdown"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.cell_type == "code"

    def test_overwrite_grade_checksum(self, preprocessors, resources):
        """Is the checksum overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["checksum"] == compute_checksum(cell)

    def test_overwrite_solution_checksum(self, preprocessors, resources):
        """Is the checksum overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["checksum"] == compute_checksum(cell)

