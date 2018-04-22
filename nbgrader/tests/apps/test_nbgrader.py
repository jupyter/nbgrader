import os
import sys

from .. import run_nbgrader, run_command
from .base import BaseTestApp


class TestNbGrader(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["--help-all"])

    def test_no_subapp(self):
        """Is the help displayed when no subapp is given?"""
        run_nbgrader([], retcode=0)

    def test_check_version(self, capfd):
        """Is the version the same regardless of how we run nbgrader?"""
        out1 = '\n'.join(
            run_command([sys.executable, "-m", "nbgrader", "--version"]).splitlines()[-3:]
        ).strip()
        out2 = '\n'.join(
            run_nbgrader(["--version"], stdout=True).splitlines()[-3:]
        ).strip()
        assert out1 == out2
