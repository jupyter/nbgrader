import os

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp
from nbgrader.utils import parse_utc


class TestNbGraderCollect(BaseTestApp):

    def _release_and_fetch(self, assignment, exchange):
        self._copy_file("files/test.ipynb", "release/ps1/p1.ipynb")
        run_command([
            'nbgrader', 'release', assignment,
            '--course', 'abc101',
            '--TransferApp.exchange_directory={}'.format(exchange)
        ])
        run_command([
            'nbgrader', 'fetch', assignment,
            '--course', 'abc101',
            '--TransferApp.exchange_directory={}'.format(exchange)
        ])

    def _submit(self, assignment, exchange):
        run_command([
            'nbgrader', 'submit', assignment,
            '--course', 'abc101',
            '--TransferApp.exchange_directory={}'.format(exchange)
        ])

    def _collect(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            'nbgrader', 'collect', assignment,
            '--course', 'abc101',
            '--TransferApp.exchange_directory={}'.format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_command(cmd, retcode=retcode)

    def _read_timestamp(self, root):
        with open(os.path.join(root, "timestamp.txt"), "r") as fh:
            timestamp = parse_utc(fh.read())
        return timestamp

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "collect", "--help-all"])

    def test_no_course_id(self, exchange):
        """Does releasing without a course id thrown an error?"""
        self._release_and_fetch("ps1", exchange)
        self._submit("ps1", exchange)
        cmd = [
            "nbgrader", "collect", "ps1",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]
        run_command(cmd, retcode=1)

    def test_collect(self, exchange):
        self._release_and_fetch("ps1", exchange)

        # try to collect when there's nothing to collect
        self._collect("ps1", exchange)
        root = os.path.join("submitted/{}/ps1".format(os.environ['USER']))
        assert os.path.isdir("submitted")
        assert not os.path.isdir(root)

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

