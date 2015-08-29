import os

from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderRelease(BaseTestApp):

    def _release(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "nbgrader", "release", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_python_module(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "release", "--help-all"])

    def test_no_course_id(self, exchange):
        """Does releasing without a course id thrown an error?"""
        cmd = [
            "nbgrader", "release", "ps1",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_python_module(cmd, retcode=1)

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
