import os
import sys
import pytest
from os.path import join, exists, isfile

from ...utils import remove
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["generate_feedback", "--help-all"])

    def test_deprecated(self, db, course_dir):
        """Can feedback be generated for an unchanged assignment?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["feedback", "ps1", "--db", db])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

    def test_single_file(self, db, course_dir):
        """Can feedback be generated for an unchanged assignment?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

    def test_student_id_exclude(self, db, course_dir):
        """Does --CourseDirectory.student_id_exclude=X exclude students?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        run_nbgrader(["db", "student", "add", "baz", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])

        for student in ["foo", "bar", "baz"]:
            self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", student, "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--CourseDirectory.student_id_exclude=bar,baz"])

        for student in ["foo", "bar", "baz"]:
            assert exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not exists(join(course_dir, "feedback", "bar", "ps1", "p1.html"))
        assert not exists(join(course_dir, "feedback", "baz", "ps1", "p1.html"))


    def test_force(self, db, course_dir):
        """Ensure the force option works properly"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["autograde", "ps1", "--db", db])

        self._make_file(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["generate_feedback", "ps1", "--db", db])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--force"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--force"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

    def test_force_f(self, db, course_dir):
        """Ensure the force option works properly"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["autograde", "ps1", "--db", db])

        self._make_file(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["generate_feedback", "ps1", "--db", db])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "-f"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--force"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

    def test_filter_notebook(self, db, course_dir):
        """Does feedback filter by notebook properly?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook still causes it to run
        remove(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that running it again doesn"t do anything
        remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook doesn"t cause it to run
        remove(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        run_nbgrader(["generate_feedback", "ps1", "--db", db])

        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, course_dir, groupshared):
        """Are permissions properly set?"""
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])
        with open("nbgrader_config.py", "a") as fh:
            if groupshared:
                fh.write("""c.CourseDirectory.groupshared = True\n""")
        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1"])

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

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.html"))
        if groupshared:
            # non-groupshared doesn't guarantee anything about directory perms
            assert self._get_permissions(join(course_dir, "feedback", "foo", "ps1")) == dirperms
        assert self._get_permissions(join(course_dir, "feedback", "foo", "ps1", "foo.html")) == perms

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])
        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1", "--GenerateFeedback.permissions=444"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.html"))
        assert self._get_permissions(join(course_dir, "feedback", "foo", "ps1", "foo.html")) == '444'

    def test_force_single_notebook(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        p1 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        p2 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_feedback", "ps1", "--notebook", "p1", "--force"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert p1 != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert p2 == self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

    def test_update_newer(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 America/Los_Angeles"
        p = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 America/Los_Angeles")
        run_nbgrader(["generate_feedback", "ps1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 America/Los_Angeles"
        assert p != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

    def test_update_newer_single_notebook(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 America/Los_Angeles"
        p1 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        p2 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 America/Los_Angeles")
        run_nbgrader(["generate_feedback", "ps1", "--notebook", "p1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 America/Los_Angeles"
        assert p1 != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert p2 == self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

    def test_autotests(self, course_dir):
        """Can feedback be generated for an assignment with autotests?"""
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])

        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        self._copy_file(join("files", "autotests.yml"), join(course_dir, "autotests.yml"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "autotest-simple.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 America/Los_Angeles"
        p1 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        p2 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 America/Los_Angeles")
        run_nbgrader(["generate_feedback", "ps1", "--notebook", "p1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 America/Los_Angeles"
        assert p1 != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert p2 == self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

    def test_single_user(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["assign", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1"])
        run_nbgrader(["generate_feedback", "ps1", "--student", "foo"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert not exists(join(course_dir, "feedback", "bar", "ps1", "p1.html"))
        assert not exists(join(course_dir, "feedback", "bar", "ps1", "p2.html"))
