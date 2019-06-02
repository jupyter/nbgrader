import os
import shutil

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderQuickStart(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["quickstart", "--help-all"])

    def test_no_course_id(self):
        """Is the help displayed when no course id is given?"""
        run_nbgrader(["quickstart"], retcode=1)

    def test_quickstart(self, fake_home_dir):
        """Is the quickstart example properly generated?"""

        run_nbgrader(["quickstart", "example"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example"], retcode=1)

        # it should succeed if --force is given
        os.remove(os.path.join("example", "nbgrader_config.py"))
        run_nbgrader(["quickstart", "example", "--force"])
        assert os.path.exists(os.path.join("example", "nbgrader_config.py"))

        # nbgrader validate should work
        os.chdir("example")
        for nb in os.listdir(os.path.join("source", "ps1")):
            if not nb.endswith(".ipynb"):
                continue
            output = run_nbgrader(["validate", os.path.join("source", "ps1", nb)], stdout=True)
            assert output.strip() == "Success! Your notebook passes all the tests."

        # nbgrader generate_assignment should work
        run_nbgrader(["generate_assignment", "ps1"])

    def test_quickstart_overwrite_course_folder_if_structure_not_present(self):
        """Is the quickstart example properly generated?"""

        run_nbgrader(["quickstart", "example_without_folder_and_config_file"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example_without_folder_and_config_file"], retcode=1)

        # should succeed if both source folder and config file are not present.
        shutil.rmtree(os.path.join("example_without_folder_and_config_file", "source"))
        os.remove(os.path.join("example_without_folder_and_config_file", "nbgrader_config.py"))

        run_nbgrader(["quickstart", "example_without_folder_and_config_file"])
        assert os.path.exists(os.path.join("example_without_folder_and_config_file", "nbgrader_config.py"))
        assert os.path.exists(os.path.join("example_without_folder_and_config_file", "source"))

        # nbgrader validate should work
        os.chdir("example_without_folder_and_config_file")
        for nb in os.listdir(os.path.join("source", "ps1")):
            if not nb.endswith(".ipynb"):
                continue
            output = run_nbgrader(["validate", os.path.join("source", "ps1", nb)], stdout=True)
            assert output.strip() == "Success! Your notebook passes all the tests."

        # nbgrader generate_assignment should work
        run_nbgrader(["generate_assignment", "ps1"])

    def test_quickstart_fails_with_source_folder_removed(self):
        """Is the quickstart example properly generated if source folder removed?"""

        run_nbgrader(["quickstart", "example_source_folder_fail"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example_source_folder_fail"], retcode=1)

        # it should succeed if source folder not present and create it
        shutil.rmtree(os.path.join("example_source_folder_fail", "source"))

        # it should fail if it already source folder or config file exists
        run_nbgrader(["quickstart", "example_source_folder_fail"], retcode=1)

    def test_quickstart_fails_with_config_file_removed(self):
        """Is the quickstart example properly generated if source folder removed?"""

        run_nbgrader(["quickstart", "example_source_folder_fail"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example_source_folder_fail"], retcode=1)

        # it should succeed if source folder not present and create it
        os.remove(os.path.join("example_source_folder_fail", "nbgrader_config.py"))

        # it should fail if it already source folder or config file exists
        run_nbgrader(["quickstart", "example_source_folder_fail"], retcode=1)

    def test_quickstart_f(self):
        """Is the quickstart example properly generated?"""

        run_nbgrader(["quickstart", "example"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example"], retcode=1)

        # it should succeed if --force is given
        os.remove(os.path.join("example", "nbgrader_config.py"))
        run_nbgrader(["quickstart", "example", "-f"])
        assert os.path.exists(os.path.join("example", "nbgrader_config.py"))

        # nbgrader validate should work
        os.chdir("example")
        for nb in os.listdir(os.path.join("source", "ps1")):
            if not nb.endswith(".ipynb"):
                continue
            output = run_nbgrader(["validate", os.path.join("source", "ps1", nb)], stdout=True)
            assert output.strip() == "Success! Your notebook passes all the tests."

        # nbgrader generate_assignment should work
        run_nbgrader(["generate_assignment", "ps1"])
