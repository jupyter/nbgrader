import os
import sys
import pytest
import traitlets

from os.path import join
from sqlalchemy.exc import InvalidRequestError
from textwrap import dedent

from ...api import Gradebook
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderGenerateSolution(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["generate_solution", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_nbgrader(["generate_solution"], retcode=1)

    def test_conflicting_args(self):
        """Is there an error if assignment is specified both in config and as an argument?"""
        run_nbgrader(["generate_solution", "--assignment", "foo", "foo"], retcode=1)

    def test_multiple_args(self):
        """Is there an error if multiple arguments are given?"""
        run_nbgrader(["generate_solution", "foo", "bar"], retcode=1)

    def test_no_assignment(self, course_dir):
        """Is an assignment does not exists it fails"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        run_nbgrader(["generate_solution", "ps1"], retcode=1)

    def test_assignment(self, course_dir):
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"])
        assert os.path.isfile(join(course_dir, "solution", "ps1", "foo.ipynb"))

    def test_single_file_bad_assignment_name(self, course_dir, temp_cwd):
        """Test that an error is thrown when the assignment name is invalid."""
        self._empty_notebook(join(course_dir, 'source', 'foo+bar', 'foo.ipynb'))
        with pytest.raises(traitlets.TraitError):
            run_nbgrader(["generate_solution", "foo+bar"])
        assert not os.path.isfile(join(course_dir, "solution", "foo+bar", "foo.ipynb"))

    def test_multiple_files(self, course_dir):
        """Can multiple files be assigned?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'bar.ipynb'))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"])
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'bar.ipynb'))

    def test_dependent_files(self, course_dir):
        """Are dependent files properly linked?"""
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'foo.csv'), 'foo')
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.csv'), 'bar')
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'bar.ipynb'))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"])

        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'bar.ipynb'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'data', 'foo.csv'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'data', 'bar.csv'))

        with open(join(course_dir, 'solution', 'ps1', 'data', 'foo.csv'), 'r') as fh:
            assert fh.read() == 'foo'
        with open(join(course_dir, 'solution', 'ps1', 'data', 'bar.csv'), 'r') as fh:
             assert fh.read() == 'bar'

    def test_force(self, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join('files', 'test.ipynb'), join(course_dir, 'source', 'ps1', 'test.ipynb'))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), "foo")
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.txt'), "bar")
        self._make_file(join(course_dir, 'source', 'ps1', 'blah.pyc'), "asdf")
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"])
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'test.ipynb'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'data', 'bar.txt'))
        assert not os.path.isfile(join(course_dir, 'solution', 'ps1', 'blah.pyc'))

        # check that it skips the existing directory
        os.remove(join(course_dir, 'solution', 'ps1', 'foo.txt'))
        run_nbgrader(["generate_solution", "ps1"])
        assert not os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))

        # force overwrite the supplemental files
        run_nbgrader(["generate_solution", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))

        # force overwrite
        os.remove(join(course_dir, 'source', 'ps1', 'foo.txt'))
        run_nbgrader(["generate_solution", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, "solution", "ps1", "test.ipynb"))
        assert os.path.isfile(join(course_dir, "solution", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "solution", "ps1", "foo.txt"))
        assert not os.path.isfile(join(course_dir, "solution", "ps1", "blah.pyc"))

    def test_force_f(self, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join('files', 'test.ipynb'), join(course_dir, 'source', 'ps1', 'test.ipynb'))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), "foo")
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.txt'), "bar")
        self._make_file(join(course_dir, 'source', 'ps1', 'blah.pyc'), "asdf")
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"])
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'test.ipynb'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'data', 'bar.txt'))
        assert not os.path.isfile(join(course_dir, 'solution', 'ps1', 'blah.pyc'))

        # check that it skips the existing directory
        os.remove(join(course_dir, 'solution', 'ps1', 'foo.txt'))
        run_nbgrader(["generate_solution", "ps1"])
        assert not os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))

        # force overwrite the supplemental files
        run_nbgrader(["generate_solution", "ps1", "-f"])
        assert os.path.isfile(join(course_dir, 'solution', 'ps1', 'foo.txt'))

        # force overwrite
        os.remove(join(course_dir, 'source', 'ps1', 'foo.txt'))
        run_nbgrader(["generate_solution", "ps1", "-f"])
        assert os.path.isfile(join(course_dir, "solution", "ps1", "test.ipynb"))
        assert os.path.isfile(join(course_dir, "solution", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "solution", "ps1", "foo.txt"))
        assert not os.path.isfile(join(course_dir, "solution", "ps1", "blah.pyc"))

    def test_fail_no_notebooks(self):
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["generate_solution", "ps1"], retcode=1)

