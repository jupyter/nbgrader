import os

from os.path import join

from .. import run_python_module
from .base import BaseTestApp
from .conftest import notwindows
from ...utils import parse_utc


@notwindows
class TestNbGraderCollect(BaseTestApp):

    def _release_and_fetch(self, assignment, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        run_python_module([
            "nbgrader", "release", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ])
        run_python_module([
            "nbgrader", "fetch", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _submit(self, assignment, exchange):
        run_python_module([
            "nbgrader", "submit", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _collect(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "nbgrader", "collect", assignment,
            "--course", "abc101",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_python_module(cmd, retcode=retcode)

    def _read_timestamp(self, root):
        with open(os.path.join(root, "timestamp.txt"), "r") as fh:
            timestamp = parse_utc(fh.read())
        return timestamp

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "collect", "--help-all"])

    def test_no_course_id(self, exchange, course_dir):
        """Does releasing without a course id thrown an error?"""
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange)
        cmd = [
            "nbgrader", "collect", "ps1",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_python_module(cmd, retcode=1)

    def test_collect(self, exchange, course_dir):
        self._release_and_fetch("ps1", exchange, course_dir)

        # try to collect when there"s nothing to collect
        self._collect("ps1", exchange)
        root = os.path.join(join(course_dir, "submitted", os.environ["USER"], "ps1"))
        assert not os.path.isdir(join(course_dir, "submitted"))

        # submit something
        self._submit("ps1", exchange)

        # try to collect it
        self._collect("ps1", exchange)
        assert os.path.isfile(os.path.join(root, "p1.ipynb"))
        assert os.path.isfile(os.path.join(root, "timestamp.txt"))
        timestamp = self._read_timestamp(root)

        # try to collect it again
        self._collect("ps1", exchange)
        assert self._read_timestamp(root) == timestamp

        # submit again
        self._submit("ps1", exchange)

        # collect again
        self._collect("ps1", exchange)
        assert self._read_timestamp(root) == timestamp

        # collect again with --update
        self._collect("ps1", exchange, ["--update"])
        assert self._read_timestamp(root) != timestamp

    def test_collect_assignment_flag(self, exchange, course_dir):
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange)

        # try to collect when there"s nothing to collect
        self._collect("--assignment=ps1", exchange)
        root = os.path.join(join(course_dir, "submitted", os.environ["USER"], "ps1"))
        assert os.path.isfile(os.path.join(root, "p1.ipynb"))
        assert os.path.isfile(os.path.join(root, "timestamp.txt"))
