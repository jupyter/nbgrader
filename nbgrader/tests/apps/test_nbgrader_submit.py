import os
import datetime
import time

from ...utils import parse_utc
from .. import run_command
from .base import BaseTestApp


class TestNbGraderSubmit(BaseTestApp):

    def _release_and_fetch(self, assignment, exchange, cache):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        run_command([
            "nbgrader", "release", assignment,
            "--course", "abc101",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])
        run_command([
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

        run_command(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "submit", "--help-all"])

    def test_no_course_id(self, exchange, cache):
        """Does releasing without a course id thrown an error?"""
        self._release_and_fetch("ps1", exchange, cache)
        cmd = [
            "nbgrader", "submit", "ps1",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_command(cmd, retcode=1)

    def test_submit(self, exchange, cache):
        self._release_and_fetch("ps1", exchange, cache)
        now = datetime.datetime.now()

        time.sleep(1)
        self._submit("ps1", exchange, cache)

        filename, = os.listdir(os.path.join(exchange, "abc101", "inbound"))
        username, assignment, timestamp1 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp1) > now
        assert os.path.isfile(os.path.join(exchange, "abc101", "inbound", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(exchange, "abc101", "inbound", filename, "timestamp.txt"))
        with open(os.path.join(exchange, "abc101", "inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp1

        filename, = os.listdir(os.path.join(cache, "abc101"))
        username, assignment, timestamp1 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp1) > now
        assert os.path.isfile(os.path.join(cache, "abc101", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(cache, "abc101", filename, "timestamp.txt"))
        with open(os.path.join(cache, "abc101", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp1

        time.sleep(1)
        self._submit("ps1", exchange, cache)

        assert len(os.listdir(os.path.join(exchange, "abc101", "inbound"))) == 2
        filename = sorted(os.listdir(os.path.join(exchange, "abc101", "inbound")))[1]
        username, assignment, timestamp2 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp2) > parse_utc(timestamp1)
        assert os.path.isfile(os.path.join(exchange, "abc101", "inbound", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(exchange, "abc101", "inbound", filename, "timestamp.txt"))
        with open(os.path.join(exchange, "abc101", "inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp2

        assert len(os.listdir(os.path.join(cache, "abc101"))) == 2
        filename = sorted(os.listdir(os.path.join(cache, "abc101")))[1]
        username, assignment, timestamp2 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp2) > parse_utc(timestamp1)
        assert os.path.isfile(os.path.join(cache, "abc101", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(cache, "abc101", filename, "timestamp.txt"))
        with open(os.path.join(cache, "abc101", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp2
