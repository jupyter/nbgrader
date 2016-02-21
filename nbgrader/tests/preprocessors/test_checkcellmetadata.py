import pytest
import os

from ...preprocessors import CheckCellMetadata
from .base import BaseTestPreprocessor
from .. import create_grade_cell, create_solution_cell

@pytest.fixture
def preprocessor():
    return CheckCellMetadata()


class TestCheckCellMetadata(BaseTestPreprocessor):

    def test_duplicate_grade_ids(self, preprocessor):
        """Check that an error is raised when there are duplicate grade ids"""
        nb = self._read_nb(os.path.join("files", "duplicate-grade-ids.ipynb"))
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_blank_grade_id(self, preprocessor):
        """Check that an error is raised when the grade id is blank"""
        nb = self._read_nb(os.path.join("files", "blank-grade-id.ipynb"))
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_invalid_grade_cell_id(self, preprocessor):
        """Check that an error is raised when the grade cell id is invalid"""
        resources = dict(grade_ids=[])

        cell = create_grade_cell("", "code", "", 1)
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_grade_cell("", "code", "a b", 1)
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_grade_cell("", "code", "a\"b", 1)
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_solution_cell("", "code", "abc-ABC_0")
        preprocessor.preprocess_cell(cell, resources, 0)

    def test_invalid_solution_cell_id(self, preprocessor):
        """Check that an error is raised when the solution id is invalid"""
        resources = dict(grade_ids=[])

        cell = create_solution_cell("", "code", "")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_solution_cell("", "code", "a b")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_solution_cell("", "code", "a\"b")
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 0)

        cell = create_solution_cell("", "code", "abc-ABC_0")
        preprocessor.preprocess_cell(cell, resources, 0)

    def test_blank_points(self, preprocessor):
        """Check that an error is raised if the points are blank"""
        nb = self._read_nb(os.path.join("files", "blank-points.ipynb"))
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_no_duplicate_grade_ids(self, preprocessor):
        """Check that no errors are raised when grade ids are unique and not blank"""
        nb = self._read_nb(os.path.join("files", "test.ipynb"))
        preprocessor.preprocess(nb, {})

    def test_code_cell_solution_grade(self, preprocessor):
        """Check that an error is not raised when a code cell is marked as both solution and grade"""
        nb = self._read_nb(os.path.join("files", "manually-graded-code-cell.ipynb"))
        preprocessor.preprocess(nb, {})

    def test_markdown_cell_grade(self, preprocessor):
        """Check that an error is raised when a markdown cell is only marked as grade"""
        nb = self._read_nb(os.path.join("files", "bad-markdown-cell-1.ipynb"))
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_markdown_cell_solution(self, preprocessor):
        """Check that an error is raised when a markdown cell is only marked as solution"""
        nb = self._read_nb(os.path.join("files", "bad-markdown-cell-2.ipynb"))
        with pytest.raises(RuntimeError):
            preprocessor.preprocess(nb, {})

    def test_non_nbgrader_cell_blank_grade_id(self, preprocessor):
        resources = dict(grade_ids=[])
        cell = create_grade_cell("", "code", "", 1)
        cell.metadata.nbgrader['grade'] = False
        new_cell, _ = preprocessor.preprocess_cell(cell, resources, 0)
        assert 'grade_id' not in new_cell.metadata.nbgrader

        resources = dict(grade_ids=[])
        cell = create_solution_cell("", "code", "")
        cell.metadata.nbgrader['solution'] = False
        new_cell, _ = preprocessor.preprocess_cell(cell, resources, 0)
        assert 'grade_id' not in new_cell.metadata.nbgrader
