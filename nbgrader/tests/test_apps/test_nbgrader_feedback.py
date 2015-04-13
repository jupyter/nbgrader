import os
import shutil

from nbgrader.api import Gradebook

from .base import TestBase
from ..utils import run_command, temp_cwd

root = os.path.dirname(__file__)

class TestNbgraderFeedback(TestBase):

    def _setup_db(self):
        dbpath = self._init_db()
        gb = Gradebook(dbpath)
        gb.add_assignment("ps1")
        gb.add_student("foo")
        return dbpath

    def test_help(self):
        """Does the help display without error?"""
        with temp_cwd():
            run_command("nbgrader feedback --help-all")

    def test_single_file(self):
        """Can feedback be generated for an unchanged assignment?"""
        with temp_cwd([os.path.join(root, "files/submitted-unchanged.ipynb")]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            run_command('nbgrader autograde ps1 --db="{}" '.format(dbpath))
            run_command('nbgrader feedback ps1 --db="{}" '.format(dbpath))

            assert os.path.exists('feedback/foo/ps1/p1.html')

    def test_force(self):
        """Ensure the force option works properly"""
        with temp_cwd([os.path.join(root, "files/submitted-unchanged.ipynb")]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1/data')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            with open("source/ps1/foo.txt", "w") as fh:
                fh.write("foo")
            with open("source/ps1/data/bar.txt", "w") as fh:
                fh.write("bar")
            run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1/data')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            with open("submitted/foo/ps1/foo.txt", "w") as fh:
                fh.write("foo")
            with open("submitted/foo/ps1/data/bar.txt", "w") as fh:
                fh.write("bar")
            run_command('nbgrader autograde ps1 --db="{}"'.format(dbpath))

            with open("autograded/foo/ps1/blah.pyc", "w") as fh:
                fh.write("asdf")
            run_command('nbgrader feedback ps1 --db="{}"'.format(dbpath))

            assert os.path.isfile("feedback/foo/ps1/p1.html")
            assert os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

            # check that it skips the existing directory
            os.remove("feedback/foo/ps1/foo.txt")
            run_command('nbgrader feedback ps1 --db="{}"'.format(dbpath))
            assert not os.path.isfile("feedback/foo/ps1/foo.txt")

            # force overwrite the supplemental files
            run_command('nbgrader feedback ps1 --db="{}" --force'.format(dbpath))
            assert os.path.isfile("feedback/foo/ps1/foo.txt")

            # force overwrite
            os.remove("autograded/foo/ps1/foo.txt")
            run_command('nbgrader feedback ps1 --db="{}" --force'.format(dbpath))
            assert os.path.isfile("feedback/foo/ps1/p1.html")
            assert not os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

    def test_filter_notebook(self):
        """Does feedback filter by notebook properly?"""
        with temp_cwd([os.path.join(root, "files/submitted-unchanged.ipynb")]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1/data')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            with open("source/ps1/foo.txt", "w") as fh:
                fh.write("foo")
            with open("source/ps1/data/bar.txt", "w") as fh:
                fh.write("bar")
            run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1/data')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            with open("submitted/foo/ps1/foo.txt", "w") as fh:
                fh.write("foo")
            with open("submitted/foo/ps1/data/bar.txt", "w") as fh:
                fh.write("bar")
            with open("submitted/foo/ps1/blah.pyc", "w") as fh:
                fh.write("asdf")
            run_command('nbgrader autograde ps1 --db="{}"'.format(dbpath))
            run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(dbpath))

            assert os.path.isfile("feedback/foo/ps1/p1.html")
            assert os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

            # check that removing the notebook still causes it to run
            os.remove("feedback/foo/ps1/p1.html")
            os.remove("feedback/foo/ps1/foo.txt")
            run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(dbpath))

            assert os.path.isfile("feedback/foo/ps1/p1.html")
            assert os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

            # check that running it again doesn't do anything
            os.remove("feedback/foo/ps1/foo.txt")
            run_command('nbgrader feedback ps1 --db="{}" --notebook "p1"'.format(dbpath))

            assert os.path.isfile("feedback/foo/ps1/p1.html")
            assert not os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")

            # check that removing the notebook doesn't cause it to run
            os.remove("feedback/foo/ps1/p1.html")
            run_command('nbgrader feedback ps1 --db="{}"'.format(dbpath))

            assert not os.path.isfile("feedback/foo/ps1/p1.html")
            assert not os.path.isfile("feedback/foo/ps1/foo.txt")
            assert os.path.isfile("feedback/foo/ps1/data/bar.txt")
            assert not os.path.isfile("feedback/foo/ps1/blah.pyc")
