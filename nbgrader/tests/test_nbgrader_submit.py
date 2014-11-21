from .base import TestBase

class TestNbgraderSubmit(TestBase):

    def test_help(self):
        self._run_command(["nbgrader", "submit", "--help-all"])
