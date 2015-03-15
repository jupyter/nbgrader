from nose.tools import assert_raises
from nbgrader.preprocessors import CheckCellMetadata

from .base import TestBase


class TestCheckCellMetadata(TestBase):

    def setup(self):
        super(TestCheckCellMetadata, self).setup()
        self.preprocessor = CheckCellMetadata()

    def test_duplicate_grade_ids(self):
        """Check that an error is raised when there are duplicate grade ids"""
        assert_raises(
            RuntimeError, 
            self.preprocessor.preprocess, 
            self.nbs["duplicate-grade-ids.ipynb"], {})

    def test_blank_grade_id(self):
        """Check that an error is raised when the grade id is blank"""
        assert_raises(
            RuntimeError,
            self.preprocessor.preprocess,
            self.nbs["blank-grade-id.ipynb"], {})

    def test_blank_points(self):
        """Check that an error is raised if the points are blank"""
        assert_raises(
            RuntimeError,
            self.preprocessor.preprocess,
            self.nbs["blank-points.ipynb"], {})

    def test_no_duplicate_grade_ids(self):
        """Check that no errors are raised when grade ids are unique and not blank"""
        self.preprocessor.preprocess(self.nbs["test.ipynb"], {})

    def test_code_cell_solution_grade(self):
        """Check that an error is raised when a code cell is marked as both solution and grade"""
        assert_raises(
            RuntimeError,
            self.preprocessor.preprocess,
            self.nbs["bad-code-cell.ipynb"], {})

    def test_markdown_cell_grade(self):
        """Check that an error is raised when a markdown cell is only marked as grade"""
        assert_raises(
            RuntimeError,
            self.preprocessor.preprocess,
            self.nbs["bad-markdown-cell-1.ipynb"], {})

    def test_markdown_cell_solution(self):
        """Check that an error is raised when a markdown cell is only marked as solution"""
        assert_raises(
            RuntimeError,
            self.preprocessor.preprocess,
            self.nbs["bad-markdown-cell-2.ipynb"], {})
