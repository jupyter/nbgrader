import os
import datetime

from nbgrader.utils import parse_utc
from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderSubmit(BaseTestApp):

    def _release(self, assignment, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        run_command(
            'nbgrader release {} '
            '--NbGraderConfig.course_id=abc101 '
            '--TransferApp.exchange_directory={} '.format(assignment, exchange))
        run_command(
            'nbgrader fetch abc101 {} '
            '--TransferApp.exchange_directory={} '.format(assignment, exchange))

    def _submit(self, assignment, exchange, flags="", retcode=0):
        run_command(
            'nbgrader submit {} abc101 '
            '--TransferApp.exchange_directory={} '
            '{}'.format(assignment, exchange, flags),
            retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader submit --help-all")

    def test_submit(self, exchange):
        self._release("ps1", exchange)
        self._submit("ps1", exchange)

        now = datetime.datetime.now()

        filename, = os.listdir(os.path.join(exchange, "abc101/inbound"))
        username, assignment, timestamp1 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp1) > now
        assert os.path.isfile(os.path.join(exchange, "abc101/inbound", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(exchange, "abc101/inbound", filename, "timestamp.txt"))

        with open(os.path.join(exchange, "abc101/inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp1

        self._submit("ps1", exchange)

        assert len(os.listdir(os.path.join(exchange, "abc101/inbound"))) == 2
        filename = sorted(os.listdir(os.path.join(exchange, "abc101/inbound")))[1]
        username, assignment, timestamp2 = filename.split("+")
        assert username == os.environ['USER']
        assert assignment == "ps1"
        assert parse_utc(timestamp2) > parse_utc(timestamp1)
        assert os.path.isfile(os.path.join(exchange, "abc101/inbound", filename, "p1.ipynb"))
        assert os.path.isfile(os.path.join(exchange, "abc101/inbound", filename, "timestamp.txt"))

        with open(os.path.join(exchange, "abc101/inbound", filename, "timestamp.txt"), "r") as fh:
            assert fh.read() == timestamp2
