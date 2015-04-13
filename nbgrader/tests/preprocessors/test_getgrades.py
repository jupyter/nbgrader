from nbgrader.preprocessors import SaveCells, SaveAutoGrades, GetGrades
from nbgrader.api import Gradebook
from IPython.nbformat.v4 import new_notebook, new_output

from .base import TestBase
from .. import create_grade_cell, create_solution_cell, create_grade_and_solution_cell


class TestGetGrades(TestBase):

    def setup(self):
        super(TestGetGrades, self).setup()
        db_url = self._init_db()
        self.gb = Gradebook(db_url)
        self.gb.add_assignment("ps0")
        self.gb.add_student("bar")

        self.preprocessor1 = SaveCells()
        self.preprocessor2 = SaveAutoGrades()
        self.preprocessor3 = GetGrades()
        self.resources = {
            "nbgrader": {
                "db_url": db_url,
                "assignment": "ps0",
                "notebook": "test",
                "student": "bar"
            }
        }

    def test_save_correct_code(self):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        assert cell.metadata.nbgrader['score'] == 1
        assert cell.metadata.nbgrader['points'] == 1
        assert 'comment' not in cell.metadata.nbgrader

    def test_save_incorrect_code(self):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1
        assert 'comment' not in cell.metadata.nbgrader

    def test_save_unchanged_code(self):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == "No response."

    def test_save_changed_code(self):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        cell.source = "hello!"
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == None

    def test_save_unchanged_markdown(self):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == "No response."

    def test_save_changed_markdown(self):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        cell.source = "hello!"
        self.preprocessor2.preprocess(nb, self.resources)
        self.preprocessor3.preprocess(nb, self.resources)

        assert cell.metadata.nbgrader['score'] == 0
        assert cell.metadata.nbgrader['points'] == 1

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert cell.metadata.nbgrader['comment'] == comment.to_dict()
        assert cell.metadata.nbgrader['comment']['comment'] == None
