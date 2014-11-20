from .base import TestBase

class TestNbgraderAutograde(TestBase):

    def test_no_args(self):
        self._run_command(["nbgrader", "autograde"])

    def test_help(self):
        self._run_command(["nbgrader", "autograde", "--help-all"])
