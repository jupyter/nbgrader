import os

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader feedback --help-all")

    def test_single_file(self, gradebook):
        """Can feedback be generated for an unchanged assignment?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}" '.format(gradebook))
        run_command('nbgrader feedback ps1 --db="{}" '.format(gradebook))

        assert os.path.exists('feedback/foo/ps1/p1.html')

    def test_force(self, gradebook):
        """Ensure the force option works properly"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        self._make_file("autograded/foo/ps1/blah.pyc", "asdf")
        run_command('nbgrader feedback ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that it skips the existing directory
        os.remove("feedback/foo/ps1/foo.txt")
        run_command('nbgrader feedback ps1 --db="{}"'.format(gradebook))
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")

        # force overwrite the supplemental files
        run_command('nbgrader feedback ps1 --db="{}" --force'.format(gradebook))
        assert os.path.isfile("feedback/foo/ps1/foo.txt")

        # force overwrite
        os.remove("autograded/foo/ps1/foo.txt")
        run_command('nbgrader feedback ps1 --db="{}" --force'.format(gradebook))
        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

    def test_filter_notebook(self, gradebook):
        """Does feedback filter by notebook properly?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))
        run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that removing the notebook still causes it to run
        os.remove("feedback/foo/ps1/p1.html")
        os.remove("feedback/foo/ps1/foo.txt")
        run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that running it again doesn't do anything
        os.remove("feedback/foo/ps1/foo.txt")
        run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

        # check that removing the notebook doesn't cause it to run
        os.remove("feedback/foo/ps1/p1.html")
        run_command('nbgrader feedback ps1 --db="{}"'.format(gradebook))

        assert not os.path.isfile("feedback/foo/ps1/p1.html")
        assert not os.path.isfile("feedback/foo/ps1/foo.txt")
        assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
        assert not os.path.isfile("feedback/foo/ps1/blah.pyc")
