from .base import TestBase
from nbgrader.api import Gradebook

import os
import shutil

class TestNbgraderFeedback(TestBase):

    def _setup_db(self):
        dbpath = self._init_db()
        gb = Gradebook(dbpath)
        gb.add_assignment("ps1")
        gb.add_student("foo")
        return dbpath

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader feedback --help-all")

    def test_single_file(self):
        """Can feedback be generated for an unchanged assignment?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb"]):
            dbpath = self._setup_db()

            os.makedirs('source/ps1')
            shutil.copy('submitted-unchanged.ipynb', 'source/ps1/p1.ipynb')
            self._run_command('nbgrader assign ps1 --db="{}" '.format(dbpath))

            os.makedirs('submitted/foo/ps1')
            shutil.move('submitted-unchanged.ipynb', 'submitted/foo/ps1/p1.ipynb')
            self._run_command('nbgrader autograde ps1 --db="{}" '.format(dbpath))
            self._run_command('nbgrader feedback ps1 --db="{}" '.format(dbpath))

            assert os.path.exists('feedback/foo/ps1/p1.html')
