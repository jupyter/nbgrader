import pytest

from IPython.nbformat.v4 import new_notebook, new_output

from nbgrader.preprocessors import SaveCells, SaveAutoGrades
from nbgrader.api import Gradebook
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import (
    create_grade_cell, create_grade_and_solution_cell, create_solution_cell)


@pytest.fixture
def preprocessors():
    return (SaveCells(), SaveAutoGrades())


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


class TestSaveAutoGrades(BaseTestPreprocessor):

    def test_grade_correct_code(self, preprocessors, gradebook, resources):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 1
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_incorrect_code(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

    def test_comment_unchanged_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == "No response."

    def test_comment_changed_code(self, preprocessors, gradebook, resources):
        """Is a changed code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == None

    def test_comment_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == "No response."

    def test_comment_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == None
