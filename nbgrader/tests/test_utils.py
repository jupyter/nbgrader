from IPython.nbformat.v4 import new_output
from nose.tools import assert_equal, assert_not_equal, assert_raises
from nbgrader import utils
from .base import TestBase


class TestUtils(TestBase):

    def test_is_grade(self):
        cell = self._create_code_cell()
        assert not utils.is_grade(cell)
        cell.metadata['nbgrader'] = {}
        assert not utils.is_grade(cell)
        cell.metadata['nbgrader']['grade'] = False
        assert not utils.is_grade(cell)
        cell.metadata['nbgrader']['grade'] = True
        assert utils.is_grade(cell)

    def test_is_solution(self):
        cell = self._create_code_cell()
        assert not utils.is_solution(cell)
        cell.metadata['nbgrader'] = {}
        assert not utils.is_solution(cell)
        cell.metadata['nbgrader']['solution'] = False
        assert not utils.is_solution(cell)
        cell.metadata['nbgrader']['solution'] = True
        assert utils.is_solution(cell)

    def test_determine_grade_code_grade(self):
        cell = self._create_grade_cell('print("test")', "code", "foo", 10)
        cell.outputs = []
        assert_equal(utils.determine_grade(cell),(10, 10))
        assert_equal(utils.determine_grade(cell, True), (10, 10))

        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        assert_equal(utils.determine_grade(cell), (0, 10))
        assert_equal(utils.determine_grade(cell, True), (0, 10))

    def test_determine_grade_markdown_grade(self):
        cell = self._create_grade_cell('test', "markdown", "foo", 10)
        assert_equal(utils.determine_grade(cell), (None, 10))
        assert_equal(utils.determine_grade(cell, True), (None, 10))

    def test_determine_grade_solution(self):
        cell = self._create_solution_cell('test', "code")
        assert_raises(ValueError, utils.determine_grade, cell)
        assert_raises(ValueError, utils.determine_grade, cell, True)

        cell = self._create_solution_cell('test', "markdown")
        assert_raises(ValueError, utils.determine_grade, cell)
        assert_raises(ValueError, utils.determine_grade, cell, True)

    def test_determine_grade_code_grade_and_solution(self):
        cell = self._create_grade_and_solution_cell('test', "code", "foo", 10)
        cell.outputs = []
        assert_equal(utils.determine_grade(cell), (10, 10))
        assert_equal(utils.determine_grade(cell, True), (10, 10))

        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        assert_equal(utils.determine_grade(cell), (0, 10))
        assert_equal(utils.determine_grade(cell, True), (0, 10))

    def test_determine_grade_markdown_grade_and_solution(self):
        cell = self._create_grade_and_solution_cell('test', "markdown", "foo", 10)
        assert_equal(utils.determine_grade(cell), (None, 10))
        assert_equal(utils.determine_grade(cell, True), (0, 10))

        cell = self._create_grade_and_solution_cell('test', "markdown", "foo", 10)
        cell.source = 'test!'
        assert_equal(utils.determine_grade(cell), (None, 10))
        assert_equal(utils.determine_grade(cell, True), (None, 10))

    def test_compute_checksum_identical(self):
        # is the same for two identical cells?
        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello", "code", "foo", 1)
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("hello", "code")
        cell2 = self._create_solution_cell("hello", "code")
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_cell_type(self):
        # does the cell type make a difference?
        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello", "markdown", "foo", 1)
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("hello", "code")
        cell2 = self._create_solution_cell("hello", "markdown")
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_whitespace(self):
        # does whitespace make no difference?
        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello ", "code", "foo", 1)
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_grade_cell("hello", "markdown", "foo", 1)
        cell2 = self._create_grade_cell("hello ", "markdown", "foo", 1)
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("hello", "code")
        cell2 = self._create_solution_cell("hello ", "code")
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("hello", "markdown")
        cell2 = self._create_solution_cell("hello ", "markdown")
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_source(self):
        # does the source make a difference?
        cell1 = self._create_grade_cell("print('hello')", "code", "foo", 1)
        cell2 = self._create_grade_cell("print( 'hello' )", "code", "foo", 1)
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_grade_cell("print('hello')", "code", "foo", 1)
        cell2 = self._create_grade_cell("print( 'hello!' )", "code", "foo", 1)
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_grade_cell("print('hello')", "markdown", "foo", 1)
        cell2 = self._create_grade_cell("print( 'hello' )", "markdown", "foo", 1)
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("print('hello')", "code")
        cell2 = self._create_solution_cell("print( 'hello' )", "code")
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("print('hello')", "code")
        cell2 = self._create_solution_cell("print( 'hello!' )", "code")
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_solution_cell("print('hello')", "markdown")
        cell2 = self._create_solution_cell("print( 'hello' )", "markdown")
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_points(self):
        # does the number of points make a difference (only for grade cells)?
        cell1 = self._create_grade_cell("hello", "code", "foo", 2)
        cell2 = self._create_grade_cell("hello", "code", "foo", 1)
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_grade_cell("hello", "code", "foo", 2)
        cell2 = self._create_grade_cell("hello", "code", "foo", 1)
        cell1.metadata.nbgrader["grade"] = False
        cell2.metadata.nbgrader["grade"] = False
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_grade_id(self):
        # does the grade id make a difference (only for grade cells)?
        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello", "code", "bar", 1)
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello", "code", "bar", 1)
        cell1.metadata.nbgrader["grade"] = False
        cell2.metadata.nbgrader["grade"] = False
        assert_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_grade_cell(self):
        # does it make a difference if grade=True?
        cell1 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2 = self._create_grade_cell("hello", "code", "foo", 1)
        cell2.metadata.nbgrader["grade"] = False
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))

    def test_compute_checksum_grade_cell(self):
        # does it make a difference if solution=True?
        cell1 = self._create_solution_cell("hello", "code")
        cell2 = self._create_solution_cell("hello", "code")
        cell2.metadata.nbgrader["solution"] = False
        assert_not_equal(utils.compute_checksum(cell1), utils.compute_checksum(cell2))
