import os

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderRelease(BaseTestApp):

    def _release(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "nbgrader", "release", assignment,
            "--NbGraderConfig.course_id=abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_command(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "release", "--help-all"])

    def test_release(self, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        self._release("ps1", exchange)
        assert os.path.isfile(os.path.join(exchange, "abc101/outbound/ps1/p1.ipynb"))

    def test_force_release(self, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        self._release("ps1", exchange)
        assert os.path.isfile(os.path.join(exchange, "abc101/outbound/ps1/p1.ipynb"))

        self._release("ps1", exchange, retcode=1)

        os.remove(os.path.join(exchange, "abc101/outbound/ps1/p1.ipynb"))
        self._release("ps1", exchange, retcode=1)

        self._release("ps1", exchange, flags=['--force'])
        assert os.path.isfile(os.path.join(exchange, "abc101/outbound/ps1/p1.ipynb"))
