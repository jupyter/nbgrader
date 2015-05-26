import os

from textwrap import dedent

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderList(BaseTestApp):

    def _release(self, assignment, exchange):
        self._copy_file("files/test.ipynb", "release/{}/p1.ipynb".format(assignment))
        run_command(
            'nbgrader release {} '
            '--NbGraderConfig.course_id=abc101 '
            '--TransferApp.exchange_directory={}'.format(assignment, exchange))

    def _fetch(self, assignment, exchange):
        run_command(
            'nbgrader fetch abc101 {} '
            '--TransferApp.exchange_directory={}'.format(assignment, exchange))

    def _submit(self, assignment, exchange):
        run_command(
            'nbgrader submit {} abc101 '
            '--TransferApp.exchange_directory={}'.format(assignment, exchange))

    def _list(self, exchange, flags='', retcode=0):
        return run_command(
            'nbgrader list abc101 '
            '--TransferApp.exchange_directory={} '
            '{}'.format(exchange, flags), retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader list --help-all")

    def test_list_released(self, exchange):
        self._release("ps1", exchange)
        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            """
        ).lstrip()

        self._release("ps2", exchange)
        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            [ListApp | INFO] abc101 ps2
            """
        ).lstrip()

    def test_list_remove_outbound(self, exchange):
        self._release("ps1", exchange)
        self._release("ps2", exchange)
        self._list(exchange, flags="--remove")
        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            """
        ).lstrip()

        self._release("ps1", exchange)
        self._release("ps2", exchange)
        self._list(exchange, flags="--remove --assignment=ps1")
        assert self._list(exchange) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps2
            """
        ).lstrip()

    def test_list_submitted(self, exchange):
        self._release("ps1", exchange)

        assert self._list(exchange, flags='--inbound') == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()

        self._fetch("ps1", exchange)
        self._submit("ps1", exchange)
        filename, = os.listdir(os.path.join(exchange, "abc101/inbound"))
        timestamp = filename.split("+")[2]
        assert self._list(exchange, flags='--inbound') == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ['USER'], timestamp)
        ).lstrip()

        self._submit("ps1", exchange)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101/inbound")))
        timestamps = [x.split("+")[2] for x in filenames]
        assert self._list(exchange, flags='--inbound') == dedent(
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

        self._list(exchange, flags="--inbound --remove")
        assert self._list(exchange, flags='--inbound') == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()

        self._submit("ps1", exchange)
        self._submit("ps2", exchange)

        self._list(exchange, flags="--inbound --remove --assignment=ps1")
        filename, = sorted(os.listdir(os.path.join(exchange, "abc101/inbound")))
        timestamp = filename.split("+")[2]
        assert self._list(exchange, flags='--inbound') == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps2 {}
            """.format(os.environ['USER'], timestamp)
        ).lstrip()
