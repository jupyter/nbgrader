import pytest

from IPython.nbformat.v4 import new_notebook, new_output

from nbgrader.preprocessors import SaveCells, SaveAutoGrades, GetGrades
from nbgrader.api import Gradebook
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import (
    create_grade_cell, create_solution_cell, create_grade_and_solution_cell)


@pytest.fixture
def preprocessors():
    return (SaveCells(), SaveAutoGrades(), GetGrades())


@pytest.fixture
def gradebook(db):
    gb = Gradebook(db)
    gb.add_assignment("ps0")
    gb.add_student("bar")
    return gb


@pytest.fixture
def resources(db):
    return {
        "nbgrader": {
            "db_url": db,
            "assignment": "ps0",
            "notebook": "test",
            "student": "bar"
        }
    }


class TestGetGrades(BaseTestPreprocessor):

    def test_save_correct_code(self, preprocessors, gradebook, resources):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader['score'] == 1
        assert cell.metadata.nbgrader['points'] == 1
        assert 'comment' not in cell.metadata.nbgrader

    def test_save_incorrect_code(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1
        assert 'comment' not in cell.metadata.nbgrader

    def test_save_unchanged_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == "No response."

    def test_save_changed_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == None

    def test_save_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == "No response."

    def test_save_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == None
