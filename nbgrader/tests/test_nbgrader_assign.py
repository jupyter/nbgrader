from .base import TestBase

class TestNbgraderAssign(TestBase):

    def test_no_args(self):
        self._run_command(["nbgrader", "assign"])

    def test_help(self):
        self._run_command(["nbgrader", "assign", "--help-all"])
