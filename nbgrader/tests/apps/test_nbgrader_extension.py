import pytest
import os
import json

from IPython.utils.py3compat import cast_unicode_py2

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderExtension(BaseTestApp):

    def _assert_is_deactivated(self, config_file, key='nbgrader/create_assignment'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        with pytest.raises(KeyError):
            config['load_extensions'][key]

    def _assert_is_activated(self, config_file, key='nbgrader/create_assignment'):
        with open(config_file, 'r') as fh:
            config = json.load(fh)
        assert config['load_extensions'][key]

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader extension --help-all")
        run_command("nbgrader extension install --help-all")
        run_command("nbgrader extension activate --help-all")
        run_command("nbgrader extension deactivate --help-all")

    def test_install_system(self, temp_dir):
        run_command("nbgrader extension install --prefix={}".format(temp_dir))

        # check the extension file were copied
        nbextension_dir = os.path.join(temp_dir, "share", "jupyter", "nbextensions", "nbgrader")
        assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader.css"))

    def test_install_user(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command("nbgrader extension install --nbextensions={}".format(nbextension_dir))

        # check the extension file were copied
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "create_assignment.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "nbgrader.css"))

    def test_activate(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command("nbgrader extension install --nbextensions={}".format(nbextension_dir))
        run_command("nbgrader extension activate --ipython-dir={}".format(temp_dir))

        # check the extension file were copied
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "create_assignment.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "nbgrader.css"))

        # check that it is activated
        config_file = os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json')
        self._assert_is_activated(config_file)

    def test_activate_custom_profile(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command("nbgrader extension install --nbextensions={}".format(nbextension_dir))
        run_command("nbgrader extension activate --ipython-dir={} --profile=foo".format(temp_dir))

        # check the extension file were copied
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "create_assignment.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "nbgrader.css"))

        # check that it is activated
        config_file = os.path.join(temp_dir, 'profile_foo', 'nbconfig', 'notebook.json')
        self._assert_is_activated(config_file)

    def test_deactivate(self, temp_dir):
        nbextension_dir = os.path.join(temp_dir, "nbextensions")
        run_command("nbgrader extension install --nbextensions={}".format(nbextension_dir))
        run_command("nbgrader extension activate --ipython-dir={}".format(temp_dir))

        # check the extension file were copied
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "create_assignment.js"))
        assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader", "nbgrader.css"))

        # check that it is activated
        config_file = os.path.join(temp_dir, 'profile_default', 'nbconfig', 'notebook.json')
        self._assert_is_activated(config_file)

        with open(config_file, 'r') as fh:
            config = json.load(fh)
        # we already assert config exist, it's fine to
        # assume 'load_extensions' is there.
        okey = 'myother_ext'
        config['load_extensions']['myother_ext'] = True

        with open(config_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

        self._assert_is_activated(config_file, key=okey)

        run_command("nbgrader extension deactivate --ipython-dir={}".format(temp_dir))

        # check that it is deactivated
        self._assert_is_deactivated(config_file)
        self._assert_is_activated(config_file, key=okey)

        with open(config_file, 'r') as fh:
            config = json.load(fh)

        del config['load_extensions']['myother_ext']

        with open(config_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

        self._assert_is_deactivated(config_file, key=okey)
