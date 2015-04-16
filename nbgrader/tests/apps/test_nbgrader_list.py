from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderList(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader list --help-all")
