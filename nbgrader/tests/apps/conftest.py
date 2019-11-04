import os
import tempfile
import shutil
import pytest
import sys

from textwrap import dedent

from _pytest.fixtures import SubRequest

from ...api import Gradebook
from ...utils import rmtree


@pytest.fixture
def db(request: SubRequest) -> str:
    path = tempfile.mkdtemp(prefix='tmp-dbdir-')
    dbpath = os.path.join(path, "nbgrader_test.db")

    def fin() -> None:
        rmtree(path)
    request.addfinalizer(fin)

    return "sqlite:///" + dbpath


@pytest.fixture
def course_dir(request: SubRequest) -> str:
    path = tempfile.mkdtemp(prefix='tmp-coursedir-')

    def fin() -> None:
        rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def temp_cwd(request: SubRequest, course_dir: str) -> str:
    orig_dir = os.getcwd()
    path = tempfile.mkdtemp(prefix='tmp-cwd-')
    os.chdir(path)

    with open("nbgrader_config.py", "w") as fh:
        fh.write(dedent(
            """
            c = get_config()
            c.CourseDirectory.root = r"{}"
            """.format(course_dir)
        ))

    def fin() -> None:
        os.chdir(orig_dir)
        rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def jupyter_config_dir(request):
    path = tempfile.mkdtemp(prefix='tmp-configdir-')

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def jupyter_data_dir(request):
    path = tempfile.mkdtemp(prefix='tmp-datadir-')

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def fake_home_dir(request, monkeypatch):
    '''
    this fixture creates a temporary home directory. This prevents existing
    nbgrader_config.py files in the user directory to interfer with the tests.
    '''
    path = tempfile.mkdtemp(prefix='tmp-homedir-')

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    monkeypatch.setenv('HOME', str(path))

    return path


@pytest.fixture
def env(request, jupyter_config_dir, jupyter_data_dir):
    env = os.environ.copy()
    env['JUPYTER_DATA_DIR'] = jupyter_data_dir
    env['JUPYTER_CONFIG_DIR'] = jupyter_config_dir
    return env


@pytest.fixture
def exchange(request):
    path = tempfile.mkdtemp(prefix='tmp-exchange-')

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def cache(request):
    path = tempfile.mkdtemp(prefix='tmp-cache-')

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    return path

notwindows = pytest.mark.skipif(
    sys.platform == 'win32',
    reason='This functionality of nbgrader is unsupported on Windows')

windows = pytest.mark.skipif(
    sys.platform != 'win32',
    reason='This test is only to be run on Windows')
