from IPython.nbformat.v4 import new_output
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

    def test_determine_grade(self):
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        cell.metadata['nbgrader']['points'] = 10
        cell.outputs = []
        assert utils.determine_grade(cell) == (10, 10)

        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        assert utils.determine_grade(cell) == (0, 10)

        cell = self._create_text_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        cell.metadata['nbgrader']['points'] = 10
        assert utils.determine_grade(cell) == (None, 10)
