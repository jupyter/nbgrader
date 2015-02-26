from nose.tools import assert_raises
from nbgrader.preprocessors import CheckGradeIds

from .base import TestBase


class TestCheckGradeIds(TestBase):

    def setup(self):
        super(TestCheckGradeIds, self).setup()
        self.preprocessor = CheckGradeIds()

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
