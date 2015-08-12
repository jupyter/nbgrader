import os

from textwrap import dedent

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderList(BaseTestApp):

    def _release(self, assignment, exchange, course="abc101"):
        self._copy_file("files/test.ipynb", "release/{}/p1.ipynb".format(assignment))
        run_command([
            "nbgrader", "release", assignment,
            "--course", course,
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _fetch(self, assignment, exchange, course="abc101"):
        run_command([
            "nbgrader", "fetch", assignment,
            "--course", course,
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _submit(self, assignment, exchange, course="abc101"):
        run_command([
            "nbgrader", "submit", assignment,
            "--course", course,
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _list(self, exchange, assignment=None, flags=None, retcode=0):
        cmd = [
            "nbgrader", "list",
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)
        if assignment is not None:
            cmd.append(assignment)

        return run_command(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "list", "--help-all"])

    def test_list_released(self, exchange):
        self._release("ps1", exchange)
        self._release("ps1", exchange, course="xyz200")
        assert self._list(exchange, "ps1", flags=["--course", "abc101"]) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            """
        ).lstrip()
        assert self._list(exchange, "ps1", flags=["--course", "xyz200"]) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] xyz200 ps1
            """
        ).lstrip()
        assert self._list(exchange, "ps1") == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            [ListApp | INFO] xyz200 ps1
            """
        ).lstrip()

        self._release("ps2", exchange)
        self._release("ps2", exchange, course="xyz200")
        assert self._list(exchange, "ps2") == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps2
            [ListApp | INFO] xyz200 ps2
            """
        ).lstrip()

        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            [ListApp | INFO] abc101 ps2
            [ListApp | INFO] xyz200 ps1
            [ListApp | INFO] xyz200 ps2
            """
        ).lstrip()

    def test_list_remove_outbound(self, exchange):
        self._release("ps1", exchange)
        self._release("ps2", exchange)
        self._list(exchange, "ps1", flags=["--remove"])
        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps2
            """
        ).lstrip()

        self._list(exchange, "ps2", flags=["--remove"])
        assert self._list(exchange, "ps2") == dedent(
            """
            [ListApp | INFO] Released assignments:
            """
        ).lstrip()

    def test_list_submitted(self, exchange):
        self._release("ps1", exchange)

        assert self._list(exchange, "ps1", flags=['--inbound']) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()

        self._fetch("ps1", exchange)
        self._submit("ps1", exchange)
        filename, = os.listdir(os.path.join(exchange, "abc101/inbound"))
        timestamp = filename.split("+")[2]
        assert self._list(exchange, "ps1", flags=['--inbound']) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ['USER'], timestamp)
        ).lstrip()

        self._submit("ps1", exchange)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101/inbound")))
        timestamps = [x.split("+")[2] for x in filenames]
        assert self._list(exchange, "ps1", flags=['--inbound']) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ['USER'], timestamps[0], os.environ['USER'], timestamps[1])
        ).lstrip()

    def test_list_remove_inbound(self, exchange):
        self._release("ps1", exchange)
        self._fetch("ps1", exchange)
        self._release("ps2", exchange)
        self._fetch("ps2", exchange)

        self._submit("ps1", exchange)
        self._submit("ps2", exchange)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101/inbound")))
        timestamps = [x.split("+")[2] for x in filenames]

        self._list(exchange, "ps1", flags=["--inbound", "--remove"])
        assert self._list(exchange, flags=['--inbound']) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps2 {}
            """.format(os.environ['USER'], timestamps[1])
        ).lstrip()

        self._submit("ps1", exchange)
        self._submit("ps2", exchange)

        self._list(exchange, "ps2", flags=["--inbound", "--remove"])
        assert self._list(exchange, "ps2", flags=['--inbound']) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()
