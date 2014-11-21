from .base import TestBase

class TestNbgraderFormgrade(TestBase):

    def test_help(self):
        self._run_command(["nbgrader", "autograde", "--help-all"])
