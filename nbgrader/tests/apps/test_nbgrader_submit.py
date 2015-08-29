import os
import datetime
import time

from os.path import join, isfile

from ...utils import parse_utc
from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderSubmit(BaseTestApp):

    def _release_and_fetch(self, assignment, exchange, cache, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        run_python_module([
            "nbgrader", "release", assignment,
            "--course", "abc101",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])
        run_python_module([
            "nbgrader", "fetch", assignment,
            "--course", "abc101",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _submit(self, assignment, exchange, cache, flags=None, retcode=0):
        cmd = [
            "nbgrader", "submit", assignment,
            "--course", "abc101",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_python_module(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "submit", "--help-all"])

    def test_no_course_id(self, exchange, cache, course_dir):
        """Does releasing without a course id thrown an error?"""
        self._release_and_fetch("ps1", exchange, cache, course_dir)
        cmd = [
            "nbgrader", "submit", "ps1",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_python_module(cmd, retcode=1)

    def test_submit(self, exchange, cache, course_dir):
        self._release_and_fetch("ps1", exchange, cache, course_dir)
        now = datetime.datetime.now()

        time.sleep(1)
        self._submit("ps1", exchange, cache)

        filename, = os.listdir(join(exchange, "abc101", "inbound"))
        username, assignment, timestamp1 = filename.split("+")
        assert username == os.environ["USER"]
        assert assignment == "ps1"
        assert parse_utc(timestamp1) > now
        assert isfile(join(exchange, "abc101", "inbound", filename, "p1.ipynb"))
        assert isfile(join(exchange, "abc101", "inbound", filename, "timestamp.txt"))
        with open(join(exchange, "abc101", "inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp1

        filename, = os.listdir(join(cache, "abc101"))
        username, assignment, timestamp1 = filename.split("+")
        assert username == os.environ["USER"]
        assert assignment == "ps1"
        assert parse_utc(timestamp1) > now
        assert isfile(join(cache, "abc101", filename, "p1.ipynb"))
        assert isfile(join(cache, "abc101", filename, "timestamp.txt"))
        with open(join(cache, "abc101", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp1

        time.sleep(1)
        self._submit("ps1", exchange, cache)

        assert len(os.listdir(join(exchange, "abc101", "inbound"))) == 2
        filename = sorted(os.listdir(join(exchange, "abc101", "inbound")))[1]
        username, assignment, timestamp2 = filename.split("+")
        assert username == os.environ["USER"]
        assert assignment == "ps1"
        assert parse_utc(timestamp2) > parse_utc(timestamp1)
        assert isfile(join(exchange, "abc101", "inbound", filename, "p1.ipynb"))
        assert isfile(join(exchange, "abc101", "inbound", filename, "timestamp.txt"))
        with open(join(exchange, "abc101", "inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp2

        assert len(os.listdir(join(cache, "abc101"))) == 2
        filename = sorted(os.listdir(join(cache, "abc101")))[1]
        username, assignment, timestamp2 = filename.split("+")
        assert username == os.environ["USER"]
        assert assignment == "ps1"
        assert parse_utc(timestamp2) > parse_utc(timestamp1)
        assert isfile(join(cache, "abc101", filename, "p1.ipynb"))
        assert isfile(join(cache, "abc101", filename, "timestamp.txt"))
        with open(join(cache, "abc101", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp2
