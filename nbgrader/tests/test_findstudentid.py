from nbgrader.preprocessors import FindStudentID
from nose.tools import assert_equal, assert_raises
from .base import TestBase


class TestFindStudentID(TestBase):

    def setup(self):
        super(TestFindStudentID, self).setup()
        self.preprocessor = FindStudentID()

    def test_student_id_given(self):
        """Test that the student id is unchanged if it is given."""
        resources = dict(
            nbgrader=dict(student="foobar"),
            metadata=dict(name="foo"))
        self.preprocessor.regexp = r".*/(?P<student_id>.+)\.ipynb"
        nb, resources = self.preprocessor.preprocess(None, resources)
        assert_equal(resources["nbgrader"]["student"], "foobar")

    def test_no_regexp_no_id(self):
        """Check that an error is raised if no id is given and no regexp is given."""
        resources = dict(nbgrader=dict())
        assert_raises(ValueError, self.preprocessor.preprocess, None, resources)

    def test_regexp_given(self):
        """Test that the student id is correctly determined from the regexp."""
        resources = dict(nbgrader=dict(), metadata=dict(name="foo", path='.'))
        self.preprocessor.regexp = r".*/(?P<student_id>.+)\.ipynb"
        nb, resources = self.preprocessor.preprocess(None, resources)
        assert_equal(resources["nbgrader"]["student"], "foo")
