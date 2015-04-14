import pytest
import os
import json

from IPython.utils.py3compat import cast_unicode_py2

from .. import run_command


def _assert_is_deactivated(config_file, key='nbgrader/create_assignment'):
    with open(config_file, 'r') as fh:
        config = json.load(fh)
    with pytest.raises(KeyError):
        config['load_extensions'][key]


def _assert_is_activated(config_file, key='nbgrader/create_assignment'):
    with open(config_file, 'r') as fh:
        config = json.load(fh)
    assert config['load_extensions'][key]


def test_install_extension(ipythondir):
    run_command(
        "python -m nbgrader --install --activate "
        "--ipython-dir={} --nbextensions={}".format(
            ipythondir, os.path.join(ipythondir, "nbextensions")))

    print(os.listdir(os.path.join(ipythondir, "nbextensions")))

    # check the extension file were copied
    nbextension_dir = os.path.join(ipythondir, "nbextensions", "nbgrader")
    assert os.path.isfile(os.path.join(nbextension_dir, "create_assignment.js"))
    assert os.path.isfile(os.path.join(nbextension_dir, "nbgrader.css"))

    # check that it is activated
    config_file = os.path.join(ipythondir, 'profile_default', 'nbconfig', 'notebook.json')
    _assert_is_activated(config_file)


def test_deactivate_extension(ipythondir):
    # check that it is activated
    config_file = os.path.join(ipythondir, 'profile_default', 'nbconfig', 'notebook.json')
    _assert_is_activated(config_file)

    with open(config_file, 'r') as fh:
        config = json.load(fh)
    # we already assert config exist, it's fine to
    # assume 'load_extensions' is there.
    okey = 'myother_ext'
    config['load_extensions']['myother_ext'] = True

    with open(config_file, 'w+') as f:
        f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

    _assert_is_activated(config_file, key=okey)

    run_command(
        "python -m nbgrader --deactivate "
        "--ipython-dir={}".format(ipythondir))

    # check that it is deactivated
    _assert_is_deactivated(config_file)
    _assert_is_activated(config_file, key=okey)

    with open(config_file, 'r') as fh:
        config = json.load(fh)

    del config['load_extensions']['myother_ext']

    with open(config_file, 'w+') as f:
        f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

    _assert_is_deactivated(config_file, key=okey)


def test_activate_extension(ipythondir):
    # check that it is deactivated
    config_file = os.path.join(ipythondir, 'profile_default', 'nbconfig', 'notebook.json')
    _assert_is_deactivated(config_file)

    run_command(
        "python -m nbgrader --activate "
        "--ipython-dir={}".format(ipythondir))

    # check that it is activated
    _assert_is_activated(config_file)
