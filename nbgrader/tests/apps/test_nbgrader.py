import os

from .. import run_command
from .base import BaseTestApp


class TestNbGrader(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "--help-all"])

    def test_no_subapp(self):
        """Is the help displayed when no subapp is given?"""
        run_command(["nbgrader"], retcode=1)

    def test_generate_config(self):
        """Is the config file properly generated?"""

        run_command(["nbgrader", "--generate-config"])
        assert os.path.isfile("nbgrader_config.py")

        # does it fail if it already exists?
        run_command(["nbgrader", "--generate-config"], retcode=1)
