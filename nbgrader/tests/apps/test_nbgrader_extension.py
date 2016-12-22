import pytest
import os
import json
import six
import sys

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderExtension(BaseTestApp):

    def _assert_is_deactivated(self, config_file, key='create_assignment/main'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        if key in config['load_extensions']:
            assert not config['load_extensions'][key]
        else:
            with pytest.raises(KeyError):
                config['load_extensions'][key]

    def _assert_is_activated(self, config_file, key='create_assignment/main'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        assert config['load_extensions'][key]

    def _assert_is_installed(self, nbextension_dir):
        assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment", "main.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment", "create_assignment.css"))

        if sys.platform != 'win32':
            assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "main.js"))
            assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "assignment_list.css"))
            assert os.path.isfile(os.path.join(nbextension_dir, "assignment_list", "assignment_list.css"))

    def _assert_is_uninstalled(self, nbextension_dir):
        assert not os.path.exists(os.path.join(nbextension_dir, "create_assignment"))

        if sys.platform != 'win32':
            assert not os.path.exists(os.path.join(nbextension_dir, "assignment_list"))

    def _activate_fake_extension(self, config_file, key):
        with open(config_file, 'r') as fh:
            config = json.load(fh)

        # we already assert config exist, it's fine to
        # assume 'load_extensions' is there.
        config['load_extensions'][key] = True

        with open(config_file, 'w+') as f:
            f.write(six.u(json.dumps(config, indent=2)))

        self._assert_is_activated(config_file, key=key)

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["extension", "--help-all"])
        run_nbgrader(["extension", "install", "--help-all"])
        run_nbgrader(["extension", "uninstall", "--help-all"])
        run_nbgrader(["extension", "activate", "--help-all"])
        run_nbgrader(["extension", "deactivate", "--help-all"])

    def test_install_system(self, jupyter_data_dir, env):
        run_nbgrader(["extension", "install", "--prefix", jupyter_data_dir], env=env)
        self._assert_is_installed(os.path.join(jupyter_data_dir, "share", "jupyter", "nbextensions"))
        run_nbgrader(["extension", "uninstall", "--prefix", jupyter_data_dir], env=env)
        self._assert_is_uninstalled(os.path.join(jupyter_data_dir, "share", "jupyter", "nbextensions"))

    def test_install_user(self, jupyter_data_dir, env):
        nbextension_dir = os.path.join(jupyter_data_dir, "nbextensions")
        run_nbgrader(["extension", "install", "--nbextensions", nbextension_dir], env=env)
        self._assert_is_installed(nbextension_dir)
        run_nbgrader(["extension", "uninstall", "--nbextensions", nbextension_dir], env=env)
        self._assert_is_uninstalled(nbextension_dir)

    def test_activate(self, jupyter_data_dir, jupyter_config_dir, env):
        nbextension_dir = os.path.join(jupyter_data_dir, "nbextensions")
        run_nbgrader(["extension", "install", "--nbextensions", nbextension_dir], env=env)
        run_nbgrader(["extension", "activate"], env=env)

        # check the extension file were copied
        self._assert_is_installed(nbextension_dir)

        # check that it is activated
        self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='create_assignment/main')
        if sys.platform != 'win32':
            self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='assignment_list/main')

    def test_deactivate(self, jupyter_data_dir, jupyter_config_dir, env):
        nbextension_dir = os.path.join(jupyter_data_dir, "nbextensions")
        run_nbgrader(["extension", "install", "--nbextensions", nbextension_dir], env=env)
        run_nbgrader(["extension", "activate"], env=env)

        # check the extension file were copied
        self._assert_is_installed(nbextension_dir)

        # check that it is activated
        self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='create_assignment/main')
        if sys.platform != 'win32':
            self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='assignment_list/main')

        # activate a fake extension
        self._activate_fake_extension(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='other_extension')
        if sys.platform != 'win32':
            self._activate_fake_extension(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='other_extension')

        run_nbgrader(["extension", "deactivate"], env=env)

        # check that it is deactivated
        self._assert_is_deactivated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='other_extension')
        if sys.platform != 'win32':
            self._assert_is_deactivated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='assignment_list/main')
            self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='other_extension')

        run_nbgrader(["extension", "activate"], env=env)

        self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='create_assignment/main')
        self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'notebook.json'), key='other_extension')
        if sys.platform != 'win32':
            self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='assignment_list/main')
            self._assert_is_activated(os.path.join(jupyter_config_dir, 'nbconfig', 'tree.json'), key='other_extension')
