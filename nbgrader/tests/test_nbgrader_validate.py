from .base import TestBase

class TestNbgraderValidate(TestBase):

    def test_no_args(self):
        self._run_command(["nbgrader", "validate"])

    def test_help(self):
        self._run_command(["nbgrader", "validate", "--help-all"])
