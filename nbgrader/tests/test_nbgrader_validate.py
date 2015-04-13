from .base import TestBase

class TestNbgraderValidate(TestBase):

    def test_help(self):
        """Does the help display without error?"""
        self._run_command("nbgrader validate --help-all")

    def test_validate_unchanged(self):
        """Does the validation fail on an unchanged notebook?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb"]):
            output = self._run_command('nbgrader validate submitted-unchanged.ipynb')
            assert output.split("\n")[0] == "VALIDATION FAILED ON 2 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_validate_changed(self):
        """Does the validation pass on an changed notebook?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            output = self._run_command('nbgrader validate submitted-changed.ipynb')
            assert output == "Success! Your notebook passes all the tests.\n"

    def test_invert_validate_unchanged(self):
        """Does the inverted validation pass on an unchanged notebook?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb"]):
            output = self._run_command('nbgrader validate submitted-unchanged.ipynb --invert')
            assert output.split("\n")[0] == "NOTEBOOK PASSED ON 1 CELL(S)!"

    def test_invert_validate_changed(self):
        """Does the inverted validation fail on a changed notebook?"""
        with self._temp_cwd(["files/submitted-changed.ipynb"]):
            output = self._run_command('nbgrader validate submitted-changed.ipynb --invert')
            assert output.split("\n")[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_grade_cell_changed(self):
        """Does the validate fail if a grade cell has changed?"""
        with self._temp_cwd(["files/submitted-grade-cell-changed.ipynb"]):
            output = self._run_command('nbgrader validate submitted-grade-cell-changed.ipynb')
            assert output.split("\n")[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_grade_cell_changed_ignore_checksums(self):
        """Does the validate pass if a grade cell has changed but we're ignoring checksums?"""
        with self._temp_cwd(["files/submitted-grade-cell-changed.ipynb"]):
            output = self._run_command(
                'nbgrader validate submitted-grade-cell-changed.ipynb '
                '--DisplayAutoGrades.ignore_checksums=True')
            assert output.split("\n")[0] == "Success! Your notebook passes all the tests."

    def test_invert_grade_cell_changed(self):
        """Does the validate fail if a grade cell has changed, even with --invert?"""
        with self._temp_cwd(["files/submitted-grade-cell-changed.ipynb"]):
            output = self._run_command('nbgrader validate submitted-grade-cell-changed.ipynb --invert')
            assert output.split("\n")[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_invert_grade_cell_changed_ignore_checksums(self):
        """Does the validate fail if a grade cell has changed with --invert and ignoring checksums?"""
        with self._temp_cwd(["files/submitted-grade-cell-changed.ipynb"]):
            output = self._run_command(
                'nbgrader validate submitted-grade-cell-changed.ipynb '
                '--invert '
                '--DisplayAutoGrades.ignore_checksums=True')
            assert output.split("\n")[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_validate_unchanged_ignore_checksums(self):
        """Does the validation fail on an unchanged notebook with ignoring checksums?"""
        with self._temp_cwd(["files/submitted-unchanged.ipynb"]):
            output = self._run_command(
                'nbgrader validate submitted-unchanged.ipynb '
                '--DisplayAutoGrades.ignore_checksums=True')
            assert output.split("\n")[0] == "VALIDATION FAILED ON 1 CELL(S)! If you submit your assignment as it is, you WILL NOT"

