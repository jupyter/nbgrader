import pytest
import os
import json

from IPython.utils.py3compat import cast_unicode_py2

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderExtension(BaseTestApp):

    def _assert_is_deactivated(self, config_file, key='create_assignment/main'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        with pytest.raises(KeyError):
            config['load_extensions'][key]

    def _assert_is_activated(self, config_file, key='create_assignment/main'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        assert config['load_extensions'][key]

    def _assert_is_installed(self, nbextension_dir):
        assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment", "main.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment", "create_assignment.css"))

        assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "main.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "assignment_list.css"))
        assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "assignment_list.css"))

    def _activate_fake_extension(self, config_file, key):
        with open(config_file, 'r') as fh:
            config = json.load(fh)

        # we already assert config exist, it's fine to
        # assume 'load_extensions' is there.
        config['load_extensions'][key] = True

        with open(config_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

        self._assert_is_activated(config_file, key=key)

    def test_help(self):
        """Does the help display without error?"""
        run_command(["nbgrader", "extension", "--help-all"])
        run_command(["nbgrader", "extension", "install", "--help-all"])
        run_command(["nbgrader", "extension", "activate", "--help-all"])
        run_command(["nbgrader", "extension", "deactivate", "--help-all"])

    def test_install_system(self, temp_dir):
        run_command(["nbgrader", "extension", "install", "--prefix", temp_dir])
        self._assert_is_installed(os.path.join(temp_dir, "share", "jupyter", "nbextensions"))

    def test_install_user(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command(["nbgrader", "extension", "install", "--nbextensions", nbextension_dir])
        self._assert_is_installed(nbextension_dir)

    def test_activate(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command(["nbgrader", "extension", "install", "--nbextensions", nbextension_dir])
        run_command(["nbgrader", "extension", "activate", "--ipython-dir", temp_dir])

        # check the extension file were copied
        self._assert_is_installed(nbextension_dir)

        # check that it is activated
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='assignment_list/main')

    def test_activate_custom_profile(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command(["nbgrader", "extension", "install", "--nbextensions", nbextension_dir])
        run_command(["nbgrader", "extension", "activate", "--ipython-dir", temp_dir, "--profile", "foo"])

        # check the extension file were copied
        self._assert_is_installed(nbextension_dir)

        # check that it is activated
        self._assert_is_activated(os.path.join(temp_dir, 'profile_foo', 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_foo', 'nbconfig', 'tree.json'), key='assignment_list/main')

    def test_deactivate(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command(["nbgrader", "extension", "install", "--nbextensions", nbextension_dir])
        run_command(["nbgrader", "extension", "activate", "--ipython-dir", temp_dir])

        # check the extension file were copied
        self._assert_is_installed(nbextension_dir)

        # check that it is activated
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='assignment_list/main')

        # activate a fake extension
        self._activate_fake_extension(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='other_extension')
        self._activate_fake_extension(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='other_extension')

        run_command(["nbgrader", "extension", "deactivate", "--ipython-dir", temp_dir])

        # check that it is deactivated
        self._assert_is_deactivated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_deactivated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='assignment_list/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='other_extension')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='other_extension')

        run_command(["nbgrader", "extension", "activate", "--ipython-dir", temp_dir])

        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='assignment_list/main')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json'), key='other_extension')
        self._assert_is_activated(os.path.join(temp_dir, 'profile_default', 'nbconfig', 'tree.json'), key='other_extension')
