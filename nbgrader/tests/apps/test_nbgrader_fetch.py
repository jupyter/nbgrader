import os

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderFetch(BaseTestApp):

    def _release(self, assignment, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        run_command(
            'nbgrader release {} '
            '--NbGraderConfig.course_id=abc101 '
            '--TransferApp.exchange_directory={} '.format(assignment, exchange))

    def _fetch(self, assignment, exchange, flags="", retcode=0):
        run_command(
            'nbgrader fetch abc101 {} '
            '--TransferApp.exchange_directory={} '
            '{}'.format(assignment, exchange, flags),
            retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader fetch --help-all")

    def test_fetch(self, exchange):
        self._release("ps1", exchange)
        self._fetch("ps1", exchange)
        assert os.path.isfile("ps1/p1.ipynb")

        # make sure it fails if the assignment already exists
        self._fetch("ps1", exchange, retcode=1)

        # make sure it fails even if the assignment is incomplete
        os.remove("ps1/p1.ipynb")
        self._fetch("ps1", exchange, retcode=1)
