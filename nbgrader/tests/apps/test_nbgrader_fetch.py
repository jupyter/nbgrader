import os

from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderFetch(BaseTestApp):

    def _release(self, assignment, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        run_python_module([
            "nbgrader", "release", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _fetch(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "nbgrader", "fetch", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_python_module(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "fetch", "--help-all"])

    def test_no_course_id(self, exchange):
        """Does releasing without a course id thrown an error?"""
        self._release("ps1", exchange)
        cmd = [
            "nbgrader", "fetch", "ps1",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_python_module(cmd, retcode=1)

    def test_fetch(self, exchange):
        self._release("ps1", exchange)
        self._fetch("ps1", exchange)
        assert os.path.isfile("ps1/p1.ipynb")

        # make sure it fails if the assignment already exists
        self._fetch("ps1", exchange, retcode=1)

        # make sure it fails even if the assignment is incomplete
        os.remove("ps1/p1.ipynb")
        self._fetch("ps1", exchange, retcode=1)
