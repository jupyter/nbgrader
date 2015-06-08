import os

from nbgrader.api import Gradebook
from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderAssign(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader assign --help-all")

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_command("nbgrader assign", 1)

    def test_conflicting_args(self):
        """Is there an error if assignment is specified both in config and as an argument?"""
        run_command("nbgrader assign --assignment=foo foo", 1)

    def test_multiple_args(self):
        """Is there an error if multiple arguments are given?"""
        run_command("nbgrader assign foo bar", 1)

    def test_no_assignment(self):
        """Is an error thrown if the assignment doesn't exist?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        run_command("nbgrader assign ps1", 1)

    def test_single_file(self):
        """Can a single file be assigned?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        run_command("nbgrader assign ps1 --create")
        assert os.path.isfile("release/ps1/foo.ipynb")

    def test_multiple_files(self):
        """Can multiple files be assigned?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._empty_notebook('source/ps1/bar.ipynb')
        run_command("nbgrader assign ps1 --create")
        assert os.path.isfile("release/ps1/foo.ipynb")
        assert os.path.isfile("release/ps1/bar.ipynb")

    def test_dependent_files(self):
        """Are dependent files properly linked?"""
        self._make_file('source/ps1/data/foo.csv', 'foo')
        self._make_file('source/ps1/data/bar.csv', 'bar')
        self._empty_notebook('source/ps1/foo.ipynb')
        self._empty_notebook('source/ps1/bar.ipynb')
        run_command("nbgrader assign ps1 --create")

        assert os.path.isfile("release/ps1/foo.ipynb")
        assert os.path.isfile("release/ps1/bar.ipynb")
        assert os.path.isfile("release/ps1/data/foo.csv")
        assert os.path.isfile("release/ps1/data/bar.csv")

        with open('release/ps1/data/foo.csv', 'r') as fh:
            assert fh.read() == 'foo'
        with open('release/ps1/data/bar.csv', 'r') as fh:
            assert fh.read() == 'bar'

    def test_save_cells(self, db):
        """Ensure cells are saved into the database"""
        self._copy_file("files/test.ipynb", "source/ps1/test.ipynb")

        gb = Gradebook(db)
        gb.add_assignment("ps1")

        run_command('nbgrader assign ps1 --db="{}"'.format(db))

        notebook = gb.find_notebook("test", "ps1")
        assert len(notebook.grade_cells) == 6

    def test_force(self):
        """Ensure the force option works properly"""
        self._copy_file("files/test.ipynb", "source/ps1/test.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        self._make_file("source/ps1/blah.pyc", "asdf")

        run_command('nbgrader assign ps1 --create')
        assert os.path.isfile("release/ps1/test.ipynb")
        assert os.path.isfile("release/ps1/foo.txt")
        assert os.path.isfile("release/ps1/data/bar.txt")
        assert not os.path.isfile("release/ps1/blah.pyc")

        # check that it skips the existing directory
        os.remove("release/ps1/foo.txt")
        run_command('nbgrader assign ps1')
        assert not os.path.isfile("release/ps1/foo.txt")

        # force overwrite the supplemental files
        run_command('nbgrader assign ps1 --force')
        assert os.path.isfile("release/ps1/foo.txt")

        # force overwrite
        os.remove("source/ps1/foo.txt")
        run_command('nbgrader assign ps1 --force')
        assert os.path.isfile("release/ps1/test.ipynb")
        assert os.path.isfile("release/ps1/data/bar.txt")
        assert not os.path.isfile("release/ps1/foo.txt")
        assert not os.path.isfile("release/ps1/blah.pyc")

    def test_permissions(self):
        """Are permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_command("nbgrader assign ps1 --create")

        assert os.path.isfile("release/ps1/foo.ipynb")
        assert os.path.isfile("release/ps1/foo.txt")
        assert self._get_permissions("release/ps1/foo.ipynb") == "644"
        assert self._get_permissions("release/ps1/foo.txt") == "644"

    def test_custom_permissions(self):
        """Are custom permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_command("nbgrader assign ps1 --create --AssignApp.permissions=666")

        assert os.path.isfile("release/ps1/foo.ipynb")
        assert os.path.isfile("release/ps1/foo.txt")
        assert self._get_permissions("release/ps1/foo.ipynb") == "666"
        assert self._get_permissions("release/ps1/foo.txt") == "666"
