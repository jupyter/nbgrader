from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderFetch(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader fetch --help-all")
