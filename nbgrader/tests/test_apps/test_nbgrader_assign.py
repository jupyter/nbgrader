import os
import shutil

from nbgrader.api import Gradebook

from .base import TestBase
from ..utils import run_command, temp_cwd

root = os.path.dirname(__file__)

class TestNbgraderAssign(TestBase):

    def test_help(self):
        """Does the help display without error?"""
        with temp_cwd():
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
        with temp_cwd():
            os.makedirs('source/ps1')
            self._empty_notebook('source/ps1/foo.ipynb')
            run_command("nbgrader assign ps1", 1)

    def test_single_file(self):
        """Can a single file be assigned?"""
        with temp_cwd():
            os.makedirs('source/ps1')
            self._empty_notebook('source/ps1/foo.ipynb')
            run_command("nbgrader assign ps1 --create")
            assert os.path.isfile("release/ps1/foo.ipynb")

    def test_multiple_files(self):
        """Can multiple files be assigned?"""
        with temp_cwd():
            os.makedirs('source/ps1')
            self._empty_notebook('source/ps1/foo.ipynb')
            self._empty_notebook('source/ps1/bar.ipynb')
            run_command("nbgrader assign ps1 --create")
            assert os.path.isfile("release/ps1/foo.ipynb")
            assert os.path.isfile("release/ps1/bar.ipynb")

    def test_dependent_files(self):
        """Are dependent files properly linked?"""
        with temp_cwd():
            os.makedirs('source/ps1/data')
            with open('source/ps1/data/foo.csv', 'w') as fh:
                fh.write('foo')
            with open('source/ps1/data//bar.csv', 'w') as fh:
                fh.write('bar')
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

    def test_save_cells(self):
        """Ensure cells are saved into the database"""
        with temp_cwd([os.path.join(root, "files/test.ipynb")]):
            os.makedirs('source/ps1')
            shutil.move("test.ipynb", "source/ps1/test.ipynb")

            dbpath = self._init_db()
            gb = Gradebook(dbpath)
            gb.add_assignment("ps1")

            run_command('nbgrader assign ps1 --db="{}"'.format(dbpath))

            notebook = gb.find_notebook("test", "ps1")
            assert len(notebook.grade_cells) == 8

    def test_force(self):
        """Ensure the force option works properly"""
        with temp_cwd([os.path.join(root, "files/test.ipynb")]):
            os.makedirs('source/ps1/data')
            shutil.move("test.ipynb", "source/ps1/test.ipynb")
            with open("source/ps1/foo.txt", "w") as fh:
                fh.write("foo")
            with open("source/ps1/data/bar.txt", "w") as fh:
                fh.write("bar")
            with open("source/ps1/blah.pyc", "w") as fh:
                fh.write("asdf")

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
