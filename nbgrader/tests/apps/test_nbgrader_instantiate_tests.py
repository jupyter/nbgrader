import os
import sys
import pytest
import traitlets

from os.path import join
from sqlalchemy.exc import InvalidRequestError
from textwrap import dedent

from ...api import Gradebook, MissingEntry
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderInstantiateTests(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["instantiate_tests", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_nbgrader(["instantiate_tests"], retcode=1)

    def test_conflicting_args(self):
        """Is there an error if assignment is specified both in config and as an argument?"""
        run_nbgrader(["instantiate_tests", "--assignment", "foo", "foo"], retcode=1)

    def test_multiple_args(self):
        """Is there an error if multiple arguments are given?"""
        run_nbgrader(["instantiate_tests", "foo", "bar"], retcode=1)

    def test_no_modify_db(self, db, course_dir):
        """Does instantiate tests avoid modifying the database?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        with Gradebook(db) as gb:
            with pytest.raises(MissingEntry):
                assignment = gb.find_assignment("ps1")

    def test_autotests_simple(self, course_dir, temp_cwd):
        """Can a notebook with simple autotests be generated with a default yaml location, and is autotest code removed?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert not os.path.isfile(join(course_dir, "instantiated", "ps1", "tests.yml"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo

    def test_autotests_simple(self, course_dir, temp_cwd):
        """Can a notebook with simple autotests be generated with an assignment-specific yaml, and is autotest code removed?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "source", "ps1", "tests.yml"))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "tests.yml"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo

    def test_autotests_needs_yaml(self, course_dir, temp_cwd):
        """Can a notebook with autotests be generated without a yaml file?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["instantiate_tests", "ps1"], retcode=1)

    def test_single_file_bad_assignment_name(self, course_dir, temp_cwd):
        """Test that an error is thrown when the assignment name is invalid."""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "foo+bar", "foo.ipynb"))
        with pytest.raises(traitlets.TraitError):
            run_nbgrader(["instantiate_tests", "foo+bar"])
        assert not os.path.isfile(join(course_dir, "instantiated", "foo+bar", "foo.ipynb"))

    def test_multiple_files(self, course_dir):
        """Can multiple files be instantiated?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "bar.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'bar.ipynb'))

    def test_dependent_files(self, course_dir):
        """Are dependent files properly linked?"""
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'foo.csv'), 'foo')
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.csv'), 'bar')
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "bar.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])

        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'bar.ipynb'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'data', 'foo.csv'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'data', 'bar.csv'))

        with open(join(course_dir, 'instantiated', 'ps1', 'data', 'foo.csv'), 'r') as fh:
            assert fh.read() == 'foo'
        with open(join(course_dir, 'instantiated', 'ps1', 'data', 'bar.csv'), 'r') as fh:
            assert fh.read() == 'bar'

    def test_force(self, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), "foo")
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.txt'), "bar")
        self._make_file(join(course_dir, 'source', 'ps1', 'blah.pyc'), "asdf")
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'test.ipynb'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'data', 'bar.txt'))
        assert not os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'blah.pyc'))

        # check that it skips the existing directory
        os.remove(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert not os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))

        # force overwrite the supplemental files
        run_nbgrader(["instantiate_tests", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))

        # force overwrite
        os.remove(join(course_dir, 'source', 'ps1', 'foo.txt'))
        run_nbgrader(["instantiate_tests", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "test.ipynb"))
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.txt"))
        assert not os.path.isfile(join(course_dir, "instantiated", "ps1", "blah.pyc"))

    def test_force_f(self, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), "foo")
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.txt'), "bar")
        self._make_file(join(course_dir, 'source', 'ps1', 'blah.pyc'), "asdf")
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'test.ipynb'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'data', 'bar.txt'))
        assert not os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'blah.pyc'))

        # check that it skips the existing directory
        os.remove(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert not os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))

        # force overwrite the supplemental files
        run_nbgrader(["instantiate_tests", "ps1", "-f"])
        assert os.path.isfile(join(course_dir, 'instantiated', 'ps1', 'foo.txt'))

        # force overwrite
        os.remove(join(course_dir, 'source', 'ps1', 'foo.txt'))
        run_nbgrader(["instantiate_tests", "ps1", "-f"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "test.ipynb"))
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.txt"))
        assert not os.path.isfile(join(course_dir, "instantiated", "ps1", "blah.pyc"))

    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, course_dir, groupshared):
        """Are permissions properly set?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), 'foo')
        with open("nbgrader_config.py", "a") as fh:
            if groupshared:
                fh.write("""c.CourseDirectory.groupshared = True\n""")
        run_nbgrader(["instantiate_tests", "ps1"])

        if not groupshared:
            if sys.platform == 'win32':
                perms = '666'
            else:
                perms = '644'
        else:
            if sys.platform == 'win32':
                perms = '666'
                dirperms = '777'
            else:
                perms = '664'
                dirperms = '2775'

        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.txt"))
        if groupshared:
            # non-groupshared doesn't make guarantees about directory perms
            assert self._get_permissions(join(course_dir, "instantiated")) == dirperms
            assert self._get_permissions(join(course_dir, "instantiated", "ps1")) == dirperms
        assert self._get_permissions(join(course_dir, "instantiated", "ps1", "foo.ipynb")) == perms
        assert self._get_permissions(join(course_dir, "instantiated", "ps1", "foo.txt")) == perms

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), 'foo')
        run_nbgrader(["instantiate_tests", "ps1", "--InstantiateTests.permissions=444"])

        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "instantiated", "ps1", "foo.ipynb")) == "444"
        assert self._get_permissions(join(course_dir, "instantiated", "ps1", "foo.txt")) == "444"

    def test_force_single_notebook(self, course_dir):
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])

        assert os.path.exists(join(course_dir, "instantiated", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "instantiated", "ps1", "p2.ipynb"))
        p1 = self._file_contents(join(course_dir, "instantiated", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "instantiated", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["instantiate_tests", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists(join(course_dir, "instantiated", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "instantiated", "ps1", "p2.ipynb"))
        assert p1 != self._file_contents(join(course_dir, "instantiated", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "instantiated", "ps1", "p2.ipynb"))

    def test_autotests_simple(self, course_dir, temp_cwd):
        """Can a notebook with simple autotests be generated, and is autotest code removed?"""
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo

    def test_autotests_fancy(self, course_dir, temp_cwd):
        """Can a more complicated autotests notebook be generated, and is autotest code removed?"""
        self._copy_file(join("files", "autotest-multi.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo

    def test_autotests_hidden(self, course_dir, temp_cwd):
        """Can a notebook with hidden autotest be generated, and is autotest/hidden sections removed?"""
        self._copy_file(join("files", "autotest-hidden.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo
        assert "HIDDEN" not in foo

    def test_autotests_hashed(self, course_dir, temp_cwd):
        """Can a notebook with hashed autotests be generated, and is hashed autotest code removed?"""
        self._copy_file(join("files", "autotest-hashed.ipynb"), join(course_dir, "source", "ps1", "foo.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))

        foo = self._file_contents(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
        assert "AUTOTEST" not in foo
        assert "HASHED" not in foo

    def test_fail_no_notebooks(self):
        run_nbgrader(["instantiate_tests", "ps1"], retcode=1)

    def test_no_metadata(self, course_dir):
        self._copy_file(join("files", "test-no-metadata-autotest.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "tests.yml"), join(course_dir, "tests.yml"))

        # it should fail because of the missing meta data, instantiatetests runs checkcellmetadata
        run_nbgrader(["instantiate_tests", "ps1"], retcode=1)

        # it should pass now that we're not enforcing metadata
        run_nbgrader(["instantiate_tests", "ps1", "--no-metadata"])
        assert os.path.exists(join(course_dir, "instantiated", "ps1", "p1.ipynb"))

    def test_trailing_slash(self, course_dir):
        """Can a single file be assigned?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        if sys.platform == 'win32':
            trailing_slash = "\\\\"
            path = course_dir.replace("\\", "\\\\") + trailing_slash
        else:
            trailing_slash = "/"
            path = course_dir + trailing_slash
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.root = "{}"\n""".format(path))
        run_nbgrader(["instantiate_tests", "ps1"])
        assert os.path.isfile(join(course_dir, "instantiated", "ps1", "foo.ipynb"))
