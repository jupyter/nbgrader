import os

from ...api import Gradebook
from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderAutograde(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "autograde", "--help-all"])

    def test_missing_student(self, gradebook):
        """Is an error thrown when the student is missing?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-changed.ipynb", "submitted/baz/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook], retcode=1)

    def test_add_missing_student(self, gradebook):
        """Can a missing student be added?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-changed.ipynb", "submitted/baz/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--create"])

        assert os.path.isfile("autograded/baz/ps1/p1.ipynb")

    def test_missing_assignment(self, gradebook):
        """Is an error thrown when the assignment is missing?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-changed.ipynb", "submitted/ps2/foo/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps2", "--db", gradebook], retcode=1)

    def test_grade(self, gradebook):
        """Can files be graded?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/submitted-changed.ipynb", "submitted/bar/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/bar/ps1/timestamp.txt")

        gb = Gradebook(gradebook)
        notebook = gb.find_submission_notebook("p1", "ps1", "foo")
        assert notebook.score == 1
        assert notebook.max_score == 7
        assert notebook.needs_manual_grade == False

        comment1 = gb.find_comment("set_a", "p1", "ps1", "foo")
        comment2 = gb.find_comment("baz", "p1", "ps1", "foo")
        comment3 = gb.find_comment("quux", "p1", "ps1", "foo")
        assert comment1.comment == "No response."
        assert comment2.comment == "No response."
        assert comment3.comment == "No response."

        notebook = gb.find_submission_notebook("p1", "ps1", "bar")
        assert notebook.score == 2
        assert notebook.max_score == 7
        assert notebook.needs_manual_grade == True

        comment1 = gb.find_comment("set_a", "p1", "ps1", "bar")
        comment2 = gb.find_comment("baz", "p1", "ps1", "bar")
        comment2 = gb.find_comment("quux", "p1", "ps1", "bar")
        assert comment1.comment == None
        assert comment2.comment == None

    def test_grade_timestamp(self, gradebook):
        """Is a timestamp correctly read in?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")

        self._copy_file("files/submitted-changed.ipynb", "submitted/bar/ps1/p1.ipynb")
        self._make_file('submitted/bar/ps1/timestamp.txt', "2015-02-01 14:58:23.948203 PST")

        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
        assert os.path.isfile("autograded/bar/ps1/timestamp.txt")

        gb = Gradebook(gradebook)
        submission = gb.find_submission('ps1', 'foo')
        assert submission.total_seconds_late > 0
        submission = gb.find_submission('ps1', 'bar')
        assert submission.total_seconds_late == 0

        # make sure it still works to run it a second time
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

    def test_force(self, gradebook):
        """Ensure the force option works properly"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that it skips the existing directory
        os.remove("autograded/foo/ps1/foo.txt")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")

        # force overwrite the supplemental files
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--force"])
        assert os.path.isfile("autograded/foo/ps1/foo.txt")

        # force overwrite
        os.remove("source/ps1/foo.txt")
        os.remove("submitted/foo/ps1/foo.txt")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--force"])
        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

    def test_filter_notebook(self, gradebook):
        """Does autograding filter by notebook properly?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that removing the notebook still causes the autograder to run
        os.remove("autograded/foo/ps1/p1.ipynb")
        os.remove("autograded/foo/ps1/foo.txt")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that running it again doesn't do anything
        os.remove("autograded/foo/ps1/foo.txt")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that removing the notebook doesn't caus the autograder to run
        os.remove("autograded/foo/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert not os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

    def test_grade_overwrite_files(self, gradebook):
        """Are dependent files properly linked and overwritten?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/data.csv", "some,data\n")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        self._make_file("submitted/foo/ps1/data.csv", "some,other,data\n")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/foo/ps1/data.csv")

        with open("autograded/foo/ps1/timestamp.txt", "r") as fh:
            contents = fh.read()
        assert contents == "2015-02-02 15:58:23.948203 PST"

        with open("autograded/foo/ps1/data.csv", "r") as fh:
            contents = fh.read()
        assert contents == "some,data\n"

    def test_side_effects(self, gradebook):
        self._copy_file("files/side-effects.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/side-effects.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/side-effect.txt")
        assert not os.path.isfile("submitted/foo/ps1/side-effect.txt")

    def test_skip_extra_notebooks(self, gradebook):
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1 copy.ipynb")
        self._copy_file("files/submitted-changed.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/p1 copy.ipynb")

    def test_permissions(self):
        """Are permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        self._make_file("source/foo/ps1/foo.txt", "foo")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])

        assert os.path.isfile("autograded/foo/ps1/foo.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert self._get_permissions("autograded/foo/ps1/foo.ipynb") == "444"
        assert self._get_permissions("autograded/foo/ps1/foo.txt") == "444"

    def test_custom_permissions(self):
        """Are custom permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        self._make_file("source/foo/ps1/foo.txt", "foo")
        run_python_module(["nbgrader", "autograde", "ps1", "--create", "--AutogradeApp.permissions=644"])

        assert os.path.isfile("autograded/foo/ps1/foo.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert self._get_permissions("autograded/foo/ps1/foo.ipynb") == "644"
        assert self._get_permissions("autograded/foo/ps1/foo.txt") == "644"

    def test_force_single_notebook(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "source/ps1/p2.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])

        assert os.path.exists("autograded/foo/ps1/p1.ipynb")
        assert os.path.exists("autograded/foo/ps1/p2.ipynb")
        p1 = self._file_contents("autograded/foo/ps1/p1.ipynb")
        p2 = self._file_contents("autograded/foo/ps1/p2.ipynb")
        assert p1 == p2

        self._empty_notebook("submitted/foo/ps1/p1.ipynb")
        self._empty_notebook("submitted/foo/ps1/p2.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists("autograded/foo/ps1/p1.ipynb")
        assert os.path.exists("autograded/foo/ps1/p2.ipynb")
        assert p1 != self._file_contents("autograded/foo/ps1/p1.ipynb")
        assert p2 == self._file_contents("autograded/foo/ps1/p2.ipynb")

    def test_update_newer(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert self._file_contents("autograded/foo/ps1/timestamp.txt") == "2015-02-02 15:58:23.948203 PST"
        p = self._file_contents("autograded/foo/ps1/p1.ipynb")

        self._empty_notebook("submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert self._file_contents("autograded/foo/ps1/timestamp.txt") == "2015-02-02 16:58:23.948203 PST"
        assert p != self._file_contents("autograded/foo/ps1/p1.ipynb")

    def test_update_newer_single_notebook(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "source/ps1/p2.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])

        assert os.path.exists("autograded/foo/ps1/p1.ipynb")
        assert os.path.exists("autograded/foo/ps1/p2.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert self._file_contents("autograded/foo/ps1/timestamp.txt") == "2015-02-02 15:58:23.948203 PST"
        p1 = self._file_contents("autograded/foo/ps1/p1.ipynb")
        p2 = self._file_contents("autograded/foo/ps1/p2.ipynb")
        assert p1 == p2

        self._empty_notebook("submitted/foo/ps1/p1.ipynb")
        self._empty_notebook("submitted/foo/ps1/p2.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--notebook", "p1"])

        assert os.path.exists("autograded/foo/ps1/p1.ipynb")
        assert os.path.exists("autograded/foo/ps1/p2.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert self._file_contents("autograded/foo/ps1/timestamp.txt") == "2015-02-02 16:58:23.948203 PST"
        assert p1 != self._file_contents("autograded/foo/ps1/p1.ipynb")
        assert p2 == self._file_contents("autograded/foo/ps1/p2.ipynb")

    def test_handle_failure(self):
        self._empty_notebook("source/ps1/p1.ipynb")
        self._empty_notebook("source/ps1/p2.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook("submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"], retcode=1)

        assert not os.path.exists("autograded/foo/ps1")

    def test_handle_failure_single_notebook(self):
        self._empty_notebook("source/ps1/p1.ipynb")
        self._empty_notebook("source/ps1/p2.ipynb")
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook("submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        run_python_module(["nbgrader", "autograde", "ps1", "--create", "--notebook", "p*"], retcode=1)

        assert os.path.exists("autograded/foo/ps1")
        assert not os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/p2.ipynb")
