from .base import TestBase
from nbgrader.api import Gradebook

from nose.tools import assert_equal

import os
import shutil
import datetime

class TestNbgraderAutograde(TestBase):

    def _setup_db(self):
        dbpath = self._init_db()
        gb = Gradebook(dbpath)
        gb.add_assignment("ps1", duedate=datetime.datetime.now())
        gb.add_student("foo")
        gb.add_student("bar")
        return dbpath

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader autograde --help-all")

    def test_missing_student(self):
        """Is an error thrown when the student is missing?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-changed.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/baz/ps1')
            shutil.move('submitted-changed.ipynb', 'submitted/baz/ps1/p1.ipynb')
            self._run_command('nbgrader autograde ps1 --db="{}" '.format(dbpath), retcode=1)

    def test_add_missing_student(self):
        """Can a missing student be added?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-changed.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/baz/ps1')
            shutil.move('submitted-changed.ipynb', 'submitted/baz/ps1/p1.ipynb')
            self._run_command('nbgrader autograde ps1 --db="{}" --create'.format(dbpath))

            assert os.path.isfile("autograded/baz/ps1/p1.ipynb")

    def test_missing_assignment(self):
        """Is an error thrown when the assignment is missing?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-changed.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/ps2/foo')
            shutil.move('submitted-changed.ipynb', 'submitted/ps2/foo/p1.ipynb')
            self._run_command('nbgrader autograde ps2 --db="{}" '.format(dbpath), retcode=1)

    def test_grade(self):
        """Can files be graded?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb", "files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            os.makedirs('submitted/bar/ps1')
            shutil.move('submitted-changed.ipynb', 'submitted/bar/ps1/p1.ipynb')
            self._run_command('nbgrader autograde ps1 --db="{}"'.format(dbpath))

            assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
            assert not os.path.isfile("autograded/foo/ps1/timestamp.txt")
            assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
            assert not os.path.isfile("autograded/bar/ps1/timestamp.txt")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("p1", "ps1", "foo")
            assert_equal(notebook.score, 1)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, False)

            comment1 = gb.find_comment(0, "p1", "ps1", "foo")
            comment2 = gb.find_comment(1, "p1", "ps1", "foo")
            assert_equal(comment1.comment, "No response.")
            assert_equal(comment2.comment, "No response.")

            notebook = gb.find_submission_notebook("p1", "ps1", "bar")
            assert_equal(notebook.score, 2)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, True)

            comment1 = gb.find_comment(0, "p1", "ps1", "bar")
            comment2 = gb.find_comment(1, "p1", "ps1", "bar")
            assert_equal(comment1.comment, None)
            assert_equal(comment2.comment, None)

    def test_grade_timestamp(self):
        """Is a timestamp correctly read in?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb", "files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            with open('submitted/foo/ps1/timestamp.txt', 'w') as fh:
                fh.write(datetime.datetime.now().isoformat())

            os.makedirs('submitted/bar/ps1')
            shutil.move('submitted-changed.ipynb', 'submitted/bar/ps1/p1.ipynb')
            with open('submitted/bar/ps1/timestamp.txt', 'w') as fh:
                fh.write((datetime.datetime.now() - datetime.timedelta(days=1)).isoformat())

            self._run_command('nbgrader autograde ps1 --db="{}"'.format(dbpath))

            assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
            assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
            assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
            assert os.path.isfile("autograded/bar/ps1/timestamp.txt")

            gb = Gradebook(dbpath)
            submission = gb.find_submission('ps1', 'foo')
            assert submission.total_seconds_late > 0
            submission = gb.find_submission('ps1', 'bar')
            assert submission.total_seconds_late == 0
