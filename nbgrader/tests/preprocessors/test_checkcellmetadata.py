import pytest
from nbgrader.preprocessors import CheckCellMetadata
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor

@pytest.fixture
def preprocessor():
    return CheckCellMetadata()


class TestCheckCellMetadata(BaseTestPreprocessor):

    def test_duplicate_grade_ids(self, preprocessor):
        """Check that an error is raised when there are duplicate grade ids"""
        nb = self._read_nb("files/duplicate-grade-ids.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_blank_grade_id(self, preprocessor):
        """Check that an error is raised when the grade id is blank"""
        nb = self._read_nb("files/blank-grade-id.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_blank_points(self, preprocessor):
        """Check that an error is raised if the points are blank"""
        nb = self._read_nb("files/blank-points.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_no_duplicate_grade_ids(self, preprocessor):
        """Check that no errors are raised when grade ids are unique and not blank"""
        nb = self._read_nb("files/test.ipynb")
        preprocessor.preprocess(nb, {})

    def test_code_cell_solution_grade(self, preprocessor):
        """Check that an error is raised when a code cell is marked as both solution and grade"""
        nb = self._read_nb("files/bad-code-cell.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_markdown_cell_grade(self, preprocessor):
        """Check that an error is raised when a markdown cell is only marked as grade"""
        nb = self._read_nb("files/bad-markdown-cell-1.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_markdown_cell_solution(self, preprocessor):
        """Check that an error is raised when a markdown cell is only marked as solution"""
        nb = self._read_nb("files/bad-markdown-cell-2.ipynb")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})
