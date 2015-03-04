from .base import TestBase
from nose.tools import assert_equal
import os

class TestNbgraderValidate(TestBase):

    def test_help(self):
        """Does the help display without error?"""
        self._run_command(["nbgrader", "validate", "--help-all"])

    def test_validate(self):
        """Does the validation pass?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            output = self._run_command('nbgrader validate submitted.ipynb')
            assert_equal(output, "Success! Your notebook passes all the tests.\n")

    def test_invert_validate(self):
        """Does the inverted validation pass?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            output = self._run_command('nbgrader validate submitted.ipynb --invert')
            assert_equal(output.split("\n")[0], "NOTEBOOK PASSED ON 1 CELL(S)!")
            
