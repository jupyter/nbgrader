import os
from os.path import join

from .. import run_python_module
from .base import BaseTestApp
from .conftest import notwindows


@notwindows
class TestNbGraderFetch(BaseTestApp):

    def _release(self, assignment, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
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

    def test_no_course_id(self, exchange, course_dir):
        """Does releasing without a course id thrown an error?"""
        self._release("ps1", exchange, course_dir)
        cmd = [
            "nbgrader", "fetch", "ps1",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_python_module(cmd, retcode=1)

    def test_fetch(self, exchange, course_dir):
        self._release("ps1", exchange, course_dir)
        self._fetch("ps1", exchange)
        assert os.path.isfile(join("ps1", "p1.ipynb"))

        # make sure it fails if the assignment already exists
        self._fetch("ps1", exchange, retcode=1)

        # make sure it fails even if the assignment is incomplete
        os.remove(join("ps1", "p1.ipynb"))
        self._fetch("ps1", exchange, retcode=1)
