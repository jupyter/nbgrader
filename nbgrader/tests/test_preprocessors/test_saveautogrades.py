from nbgrader.preprocessors import SaveCells, SaveAutoGrades
from nbgrader.api import Gradebook
from IPython.nbformat.v4 import new_notebook, new_output

from .base import TestBase


class TestSaveAutoGrades(TestBase):

    def setup(self):
        super(TestSaveAutoGrades, self).setup()
        db_url = self._init_db()
        self.gb = Gradebook(db_url)
        self.gb.add_assignment("ps0")
        self.gb.add_student("bar")

        self.preprocessor1 = SaveCells()
        self.preprocessor2 = SaveAutoGrades()
        self.resources = {
            "nbgrader": {
                "db_url": db_url,
                "assignment": "ps0",
                "notebook": "test",
                "student": "bar"
            }
        }

    def test_grade_correct_code(self):
        """Is a passing code cell correctly graded?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)

        grade_cell = self.gb.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 1
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_incorrect_code(self):
        """Is a failing code cell correctly graded?"""
        cell = self._create_grade_cell("hello", "code", "foo", 1)
        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)

        grade_cell = self.gb.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_unchanged_markdown(self):
        """Is an unchanged markdown cell correctly graded?"""
        cell = self._create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)

        grade_cell = self.gb.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_changed_markdown(self):
        """Is a changed markdown cell correctly graded?"""
        cell = self._create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        cell.source = "hello!"
        self.preprocessor2.preprocess(nb, self.resources)

        grade_cell = self.gb.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

    def test_comment_unchanged_code(self):
        """Is an unchanged code cell given the correct comment?"""
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == "No response."

    def test_comment_changed_code(self):
        """Is a changed code cell given the correct comment?"""
        cell = self._create_solution_cell("hello", "code")
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        cell.source = "hello!"
        self.preprocessor2.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == None

    def test_comment_unchanged_markdown(self):
        """Is an unchanged markdown cell given the correct comment?"""
        cell = self._create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        self.preprocessor2.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == "No response."

    def test_comment_changed_markdown(self):
        """Is a changed markdown cell given the correct comment?"""
        cell = self._create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        self.preprocessor1.preprocess(nb, self.resources)
        self.gb.add_submission("ps0", "bar")
        cell.source = "hello!"
        self.preprocessor2.preprocess(nb, self.resources)

        comment = self.gb.find_comment(0, "test", "ps0", "bar")
        assert comment.comment == None
