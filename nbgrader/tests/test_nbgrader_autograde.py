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
        gb.add_assignment("Problem Set 1")
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
            self._run_command(
                'nbgrader autograde submitted-changed.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1"'.format(dbpath),
                retcode=1)

    def test_missing_assignment(self):
        """Is an error thrown when the assignment is missing?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted-changed.ipynb '
                '--db="{}" '
                '--student=foo'.format(dbpath),
                retcode=1)

    def test_single_file(self):
        """Can a single file be graded?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb", "files/submitted-changed.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted-unchanged.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=foo'.format(dbpath))
            self._run_command(
                'nbgrader autograde submitted-changed.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=bar'.format(dbpath))

            assert os.path.isfile("submitted-unchanged.nbconvert.ipynb")
            assert os.path.isfile("submitted-changed.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, False)

            comment1 = gb.find_comment(0, "teacher", "Problem Set 1", "foo")
            comment2 = gb.find_comment(1, "teacher", "Problem Set 1", "foo")
            assert_equal(comment1.comment, "No response.")
            assert_equal(comment2.comment, "No response.")

            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "bar")
            assert_equal(notebook.score, 2)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, True)

            comment1 = gb.find_comment(0, "teacher", "Problem Set 1", "bar")
            comment2 = gb.find_comment(1, "teacher", "Problem Set 1", "bar")
            assert_equal(comment1.comment, None)
            assert_equal(comment2.comment, None)

    def test_overwrite(self):
        """Can a single file be graded and overwrite cells?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb", "files/submitted-changed.ipynb"]):
            shutil.copy('submitted-unchanged.ipynb', 'teacher.ipynb')
            dbpath = self._setup_db()

            # first assign it and save the cells into the database
            self._run_command(
                'nbgrader assign teacher.ipynb '
                '--save-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '.format(dbpath))

            # now run the autograder
            self._run_command(
                'nbgrader autograde submitted-unchanged.ipynb '
                '--overwrite-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=foo'.format(dbpath))
            self._run_command(
                'nbgrader autograde submitted-changed.ipynb '
                '--overwrite-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=bar'.format(dbpath))

            assert os.path.isfile("submitted-unchanged.nbconvert.ipynb")
            assert os.path.isfile("submitted-changed.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, False)

            comment1 = gb.find_comment(0, "teacher", "Problem Set 1", "foo")
            comment2 = gb.find_comment(1, "teacher", "Problem Set 1", "foo")
            assert_equal(comment1.comment, "No response.")
            assert_equal(comment2.comment, "No response.")

            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "bar")
            assert_equal(notebook.score, 2)
            assert_equal(notebook.max_score, 4)
            assert_equal(notebook.needs_manual_grade, True)

            comment1 = gb.find_comment(0, "teacher", "Problem Set 1", "bar")
            comment2 = gb.find_comment(1, "teacher", "Problem Set 1", "bar")
            assert_equal(comment1.comment, None)
            assert_equal(comment2.comment, None)

    def test_timestamp(self):
        """Can the timestamp on a submission be set?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            now = datetime.datetime.now().isoformat()
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted-changed.ipynb '
                '--timestamp="{}" '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(now, dbpath))

            assert os.path.isfile("submitted-changed.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            submission = gb.find_submission("Problem Set 1", "foo")
            assert_equal(submission.timestamp.isoformat(), now)
