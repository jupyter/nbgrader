from .base import TestBase
from nbgrader.api import Gradebook

from nose.tools import assert_equal

import os
import shutil

class TestNbgraderAutograde(TestBase):

    def _setup_db(self):
        dbpath = self._init_db()
        gb = Gradebook(dbpath)
        gb.add_assignment("Problem Set 1")
        gb.add_student("foo")
        return dbpath

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader autograde --help-all")

    def test_missing_student(self):
        """Is an error thrown when the student is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1"'.format(dbpath),
                retcode=1)

    def test_missing_assignment(self):
        """Is an error thrown when the assignment is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--student=foo'.format(dbpath),
                retcode=1)

    def test_single_file(self):
        """Can a single file be graded?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(dbpath))

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("submitted", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, True, "should need manual grade")

    def test_overwrite(self):
        """Can a single file be graded and overwrite cells?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            shutil.move('submitted.ipynb', 'teacher.ipynb')
            dbpath = self._setup_db()

            # first assign it and save the cells into the database
            self._run_command(
                'nbgrader assign teacher.ipynb '
                '--save-cells '
                '--output=submitted.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '.format(dbpath))

            # now run the autograder
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--overwrite-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(dbpath))

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("submitted", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, True, "should need manual grade")
