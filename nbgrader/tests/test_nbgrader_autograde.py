from .base import TestBase
from nbgrader.api import Gradebook, Assignment, Student

from nose.tools import assert_equal

import os
import shutil

class TestNbgraderAutograde(TestBase):

    def _setup_db(self):
        gb = Gradebook('nbgrader_test')
        gb.client.drop_database('nbgrader_test')
        assignment = Assignment(assignment_id="Problem Set 1")
        gb.add_assignment(assignment)
        student = Student(student_id="foo")
        gb.add_student(student)

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader autograde --help-all")

    def test_missing_student(self):
        """Is an error thrown when the student is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db=nbgrader_test '
                '--assignment="Problem Set 1"',
                retcode=1)

    def test_missing_assignment(self):
        """Is an error thrown when the assignment is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db=nbgrader_test '
                '--student=foo',
                retcode=1)

    def test_single_file(self):
        """Can a single file be graded?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db=nbgrader_test '
                '--assignment="Problem Set 1" '
                '--student=foo')

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook("nbgrader_test")
            assignment = gb.find_assignment(assignment_id="Problem Set 1")
            student = gb.find_student(student_id="foo")
            notebook = gb.find_notebook(notebook_id="submitted", assignment=assignment, student=student)
            score = gb.notebook_score(notebook=notebook)
            assert_equal(score["score"], 1, "autograded score is incorrect")
            assert_equal(score["max_score"], 3, "maximum score is incorrect")
            assert_equal(score["needs_manual_grade"], True, "should need manual grade")

    def test_overwrite(self):
        """Can a single file be graded and overwrite cells?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            shutil.move('submitted.ipynb', 'teacher.ipynb')
            self._setup_db()

            # first assign it and save the cells into the database
            self._run_command(
                'nbgrader assign teacher.ipynb '
                '--save-cells '
                '--output=submitted.ipynb '
                '--db=nbgrader_test '
                '--assignment="Problem Set 1" ')

            # now run the autograder
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--overwrite-cells '
                '--db=nbgrader_test '
                '--assignment="Problem Set 1" '
                '--student=foo')

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook("nbgrader_test")
            assignment = gb.find_assignment(assignment_id="Problem Set 1")
            student = gb.find_student(student_id="foo")
            notebook = gb.find_notebook(notebook_id="submitted", assignment=assignment, student=student)
            score = gb.notebook_score(notebook=notebook)
            assert_equal(score["score"], 1, "autograded score is incorrect")
            assert_equal(score["max_score"], 3, "maximum score is incorrect")
            assert_equal(score["needs_manual_grade"], True, "should need manual grade")
