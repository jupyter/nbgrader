from .base import TestBase
from nbgrader.api import Gradebook

import os

class TestNbgraderFeedback(TestBase):

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
            self._run_command("nbgrader feedback --help-all")

    def test_single_file(self):
        """Can feedback be generated for an unchanged assignment?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted-unchanged.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=foo'.format(dbpath))

            self._run_command(
                'nbgrader feedback submitted-unchanged.nbconvert.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=foo'.format(dbpath))

            assert os.path.exists('submitted-unchanged.nbconvert.nbconvert.html')
