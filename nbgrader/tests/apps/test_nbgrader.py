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
        run_nbgrader([], retcode=1)

    def test_generate_config(self):
        """Is the config file properly generated?"""

        # it already exists, because we create it in conftest.py
        os.remove("nbgrader_config.py")

        # try recreating it
        run_nbgrader(["--generate-config"])
        assert os.path.isfile("nbgrader_config.py")

        # does it fail if it already exists?
        run_nbgrader(["--generate-config"], retcode=1)

    def test_check_version(self, capfd):
        """Is the version the same regardless of how we run nbgrader?"""
        if sys.platform == 'win32':
            out1 = "\r\n".join(run_command(["nbgrader.cmd", "--version"]).split("\r\n")[2:])
        else:
            out1 = run_command(["nbgrader", "--version"])
        out2 = run_nbgrader(["--version"], stdout=True)
        assert out1 == out2
