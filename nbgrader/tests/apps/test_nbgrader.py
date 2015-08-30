import os

from .. import run_python_module, run_command
from .base import BaseTestApp


class TestNbGrader(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "--help-all"])

    def test_no_subapp(self):
        """Is the help displayed when no subapp is given?"""
        run_python_module(["nbgrader"], retcode=1)

    def test_generate_config(self):
        """Is the config file properly generated?"""

        # it already exists, because we create it in conftest.py
        os.remove("nbgrader_config.py")

        # try recreating it
        run_python_module(["nbgrader", "--generate-config"])
        assert os.path.isfile("nbgrader_config.py")

        # does it fail if it already exists?
        run_python_module(["nbgrader", "--generate-config"], retcode=1)

    def test_check_version(self):
        """Is the version the same regardless of how we run nbgrader?"""
        out1 = run_command(["nbgrader", "--version"])
        out2 = run_python_module(["nbgrader", "--version"])
        assert out1 == out2
