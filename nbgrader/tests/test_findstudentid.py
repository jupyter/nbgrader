from nbgrader.preprocessors import FindStudentID
from nose.tools import assert_equal, assert_raises
from .base import TestBase


class TestFindStudentID(TestBase):

    def setup(self):
        super(TestFindStudentID, self).setup()
        self.preprocessor = FindStudentID()

    def test_student_id_given(self):
        """Test that the student id is unchanged if it is given."""
        resources = dict(nbgrader=dict(student_id="foo"))
        nb, resources = self.preprocessor.preprocess(None, resources)
        assert_equal(resources["nbgrader"]["student_id"], "foo")

    def test_no_regexp_no_id(self):
        """Check that an error is raised if no id is given and no regexp is given."""
        assert_raises(ValueError, self.preprocessor.preprocess, None, {})

    def test_regexp_given(self):
        """Test that the student id is unchanged if it is given."""
        resources = dict(metadata=dict(name="foobar", path="."))
        self.preprocessor.regexp = r".*/(?P<student_id>.+)\.ipynb"
        nb, resources = self.preprocessor.preprocess(None, resources)
        assert_equal(resources["nbgrader"]["student_id"], "foobar")
