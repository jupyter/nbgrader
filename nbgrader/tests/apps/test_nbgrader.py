import os

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


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

        with open("nbgrader_config.py", "w") as fh:
            fh.write("foo")

        run_command(["nbgrader", "--generate-config"], retcode=1)
        run_command(["nbgrader", "--generate-config", "--overwrite"])

        with open("nbgrader_config.py", "r") as fh:
            contents = fh.read()

        assert contents != "foo"
