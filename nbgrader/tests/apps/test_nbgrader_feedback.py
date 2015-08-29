import os

from .. import run_command
from .base import BaseTestApp


class TestNbGraderFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "feedback", "--help-all"])

    def test_single_file(self, gradebook):
        """Can feedback be generated for an unchanged assignment?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_command(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_command(["nbgrader", "autograde", "ps1", "--db", gradebook])
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert os.path.exists('feedback/foo/ps1/p1.html')

    def test_force(self, gradebook):
        """Ensure the force option works properly"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        run_command(["nbgrader", "autograde", "ps1", "--db", gradebook])

        self._make_file("autograded/foo/ps1/blah.pyc", "asdf")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that it skips the existing directory
        os.remove("feedback/foo/ps1/foo.txt")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook])
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")

        # force overwrite the supplemental files
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook, "--force"])
        assert os.path.isfile("feedback/foo/ps1/foo.txt")

        # force overwrite
        os.remove("autograded/foo/ps1/foo.txt")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook, "--force"])
        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

    def test_filter_notebook(self, gradebook):
        """Does feedback filter by notebook properly?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_command(["nbgrader", "autograde", "ps1", "--db", gradebook])
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that removing the notebook still causes it to run
        os.remove("feedback/foo/ps1/p1.html")
        os.remove("feedback/foo/ps1/foo.txt")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that running it again doesn't do anything
        os.remove("feedback/foo/ps1/foo.txt")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that removing the notebook doesn't cause it to run
        os.remove("feedback/foo/ps1/p1.html")
        run_command(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert not os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

    def test_permissions(self):
        """Are permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        run_command(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        run_command(["nbgrader", "autograde", "ps1", "--create"])
        run_command(["nbgrader", "feedback", "ps1"])

        assert os.path.isfile("feedback/foo/ps1/foo.html")
        assert self._get_permissions("feedback/foo/ps1/foo.html") == "444"

    def test_custom_permissions(self):
        """Are custom permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        run_command(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        run_command(["nbgrader", "autograde", "ps1", "--create"])
        run_command(["nbgrader", "feedback", "ps1", "--FeedbackApp.permissions=644"])

        assert os.path.isfile("feedback/foo/ps1/foo.html")
        assert self._get_permissions("feedback/foo/ps1/foo.html") == "644"

    def test_force_single_notebook(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "source/ps1/p2.ipynb")
        run_command(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        run_command(["nbgrader", "autograde", "ps1", "--create"])
        run_command(["nbgrader", "feedback", "ps1"])

        assert os.path.exists("feedback/foo/ps1/p1.html")
        assert os.path.exists("feedback/foo/ps1/p2.html")
        p1 = self._file_contents("feedback/foo/ps1/p1.html")
        p2 = self._file_contents("feedback/foo/ps1/p2.html")

        self._empty_notebook("autograded/foo/ps1/p1.ipynb")
        self._empty_notebook("autograded/foo/ps1/p2.ipynb")
        run_command(["nbgrader", "feedback", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists("feedback/foo/ps1/p1.html")
        assert os.path.exists("feedback/foo/ps1/p2.html")
        assert p1 != self._file_contents("feedback/foo/ps1/p1.html")
        assert p2 == self._file_contents("feedback/foo/ps1/p2.html")

    def test_update_newer(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        run_command(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        run_command(["nbgrader", "autograde", "ps1", "--create"])
        run_command(["nbgrader", "feedback", "ps1"])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/timestamp.txt")
        assert self._file_contents("feedback/foo/ps1/timestamp.txt") == "2015-02-02 15:58:23.948203 PST"
        p = self._file_contents("feedback/foo/ps1/p1.html")

        self._empty_notebook("autograded/foo/ps1/p1.ipynb")
        self._make_file('autograded/foo/ps1/timestamp.txt', "2015-02-02 16:58:23.948203 PST")
        run_command(["nbgrader", "feedback", "ps1"])

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/timestamp.txt")
        assert self._file_contents("feedback/foo/ps1/timestamp.txt") == "2015-02-02 16:58:23.948203 PST"
        assert p != self._file_contents("feedback/foo/ps1/p1.html")

    def test_update_newer_single_notebook(self):
        self._copy_file("files/test.ipynb", "source/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "source/ps1/p2.ipynb")
        run_command(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/test.ipynb", "submitted/foo/ps1/p2.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        run_command(["nbgrader", "autograde", "ps1", "--create"])
        run_command(["nbgrader", "feedback", "ps1"])

        assert os.path.exists("feedback/foo/ps1/p1.html")
        assert os.path.exists("feedback/foo/ps1/p2.html")
        assert os.path.isfile("feedback/foo/ps1/timestamp.txt")
        assert self._file_contents("feedback/foo/ps1/timestamp.txt") == "2015-02-02 15:58:23.948203 PST"
        p1 = self._file_contents("feedback/foo/ps1/p1.html")
        p2 = self._file_contents("feedback/foo/ps1/p2.html")

        self._empty_notebook("autograded/foo/ps1/p1.ipynb")
        self._empty_notebook("autograded/foo/ps1/p2.ipynb")
        self._make_file('autograded/foo/ps1/timestamp.txt', "2015-02-02 16:58:23.948203 PST")
        run_command(["nbgrader", "feedback", "ps1", "--notebook", "p1"])

        assert os.path.exists("feedback/foo/ps1/p1.html")
        assert os.path.exists("feedback/foo/ps1/p2.html")
        assert os.path.isfile("feedback/foo/ps1/timestamp.txt")
        assert self._file_contents("feedback/foo/ps1/timestamp.txt") == "2015-02-02 16:58:23.948203 PST"
        assert p1 != self._file_contents("feedback/foo/ps1/p1.html")
        assert p2 == self._file_contents("feedback/foo/ps1/p2.html")
