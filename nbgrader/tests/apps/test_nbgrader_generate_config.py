import os

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderGenerateConfig(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["generate_config", "--help-all"])

    def test_generate_config(self):
        """Is the config file properly generated?"""

        # it already exists, because we create it in conftest.py
        os.remove("nbgrader_config.py")

        # try recreating it
        run_nbgrader(["generate_config"])
        assert os.path.isfile("nbgrader_config.py")

        with open("nbgrader_config.py") as f:
            contents = f.read()

        # This was missing in issue #1089
        assert "AssignLatePenalties" in contents

        # does it fail if it already exists?
        run_nbgrader(["generate_config"], retcode=1)
