import pytest
import tempfile
import os
import shutil
import subprocess as sp
import logging
import time
import sys
import signal

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from textwrap import dedent

from nbformat import write as write_nb
from nbformat.v4 import new_notebook

from .. import copy_coverage_files, get_free_ports
from ...utils import rmtree


@pytest.fixture(scope="module")
def tempdir(request):
    tempdir = tempfile.mkdtemp()
    origdir = os.getcwd()
    os.chdir(tempdir)

    def fin():
        os.chdir(origdir)
        rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="module")
def coursedir(request):
    tempdir = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="module")
def jupyter_config_dir(request):
    jupyter_config_dir = tempfile.mkdtemp()

    def fin():
        rmtree(jupyter_config_dir)
    request.addfinalizer(fin)

    return jupyter_config_dir

@pytest.fixture(scope="module")
def jupyter_data_dir(request):
    jupyter_data_dir = tempfile.mkdtemp()

    def fin():
        rmtree(jupyter_data_dir)
    request.addfinalizer(fin)

    return jupyter_data_dir


@pytest.fixture(scope="module")
def exchange(request):
    exchange = tempfile.mkdtemp()

    def fin():
        if os.path.exists(exchange):
            rmtree(exchange)
    request.addfinalizer(fin)

    return exchange


@pytest.fixture(scope="module")
def cache(request):
    cache = tempfile.mkdtemp()

    def fin():
        rmtree(cache)
    request.addfinalizer(fin)

    return cache


@pytest.fixture(scope="module")
def class_files(coursedir):
    # copy files from the user guide
    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source")
    shutil.copytree(os.path.join(os.path.dirname(__file__), source_path), os.path.join(coursedir, "source"))

    # rename to old names -- we do this rather than changing all the tests
    # because I want the tests to operate on files with spaces in the names
    os.rename(os.path.join(coursedir, "source", "ps1"), os.path.join(coursedir, "source", "Problem Set 1"))
    os.rename(os.path.join(coursedir, "source", "Problem Set 1", "problem1.ipynb"), os.path.join(coursedir, "source", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(os.path.join(coursedir, "source", "Problem Set 1", "problem2.ipynb"), os.path.join(coursedir, "source", "Problem Set 1", "Problem 2.ipynb"))

    # create a fake ps1
    os.mkdir(os.path.join(coursedir, "source", "ps.01"))
    with open(os.path.join(coursedir, "source", "ps.01", "problem 1.ipynb"), "w") as fh:
        write_nb(new_notebook(), fh, 4)

    return coursedir


@pytest.fixture(scope="module")
def port():
    nbserver_port, = get_free_ports(1)
    return nbserver_port


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, coursedir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    env = os.environ.copy()
    env['JUPYTER_CONFIG_DIR'] = jupyter_config_dir
    env['JUPYTER_DATA_DIR'] = jupyter_data_dir
    env['HOME'] = tempdir

    sp.Popen([sys.executable, "-m", "jupyter", "nbextension", "install", "--user", "--py", "nbgrader"], env=env)
    sp.Popen([sys.executable, "-m", "jupyter", "nbextension", "enable", "--user", "--py", "nbgrader"], env=env)
    sp.Popen([sys.executable, "-m", "jupyter", "serverextension", "enable", "--user", "--py", "nbgrader"], env=env)

    # create nbgrader_config.py file
    if sys.platform != 'win32':
        with open('nbgrader_config.py', 'w') as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.TransferApp.exchange_directory = '{}'
                c.TransferApp.cache_directory = '{}'
                c.Execute.execute_retries = 4
                c.NbGrader.course_directory = '{}'
                c.NbGrader.db_assignments = [dict(name="Problem Set 1"), dict(name="ps.01")]
                c.NbGrader.db_students = [
                    dict(id="Bitdiddle", first_name="Ben", last_name="B"),
                    dict(id="Hacker", first_name="Alyssa", last_name="H"),
                    dict(id="Reasoner", first_name="Louis", last_name="R")
                ]
                """.format(exchange, cache, coursedir)
            ))

    kwargs = dict(env=env)
    if sys.platform == 'win32':
        kwargs['creationflags'] = sp.CREATE_NEW_PROCESS_GROUP

    nbserver = sp.Popen([
        sys.executable, "-m", "jupyter", "notebook",
        "--no-browser",
        "--NotebookApp.token=''",  # Notebook >=4.3
        "--port", str(port)], **kwargs)

    def fin():
        if sys.platform == 'win32':
            nbserver.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            nbserver.terminate()

        for i in range(10):
            retcode = nbserver.poll()
            if retcode is not None:
                break
            time.sleep(0.1)

        if retcode is None:
            print("couldn't shutdown notebook server, force killing it")
            nbserver.kill()

        nbserver.wait()
        copy_coverage_files()

        # wait a short period of time for kernels to finish shutting down
        time.sleep(1)

    request.addfinalizer(fin)

    return nbserver


@pytest.fixture
def browser(request, tempdir, nbserver):
    shutil.copy(os.path.join(os.path.dirname(__file__), "files", "blank.ipynb"), os.path.join(tempdir, "blank.ipynb"))

    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.WARNING)

    capabilities = DesiredCapabilities.PHANTOMJS
    capabilities['loggingPrefs'] = {'browser': 'ALL'}
    browser = webdriver.PhantomJS(
        service_args=['--cookies-file=/dev/null'],
        desired_capabilities=capabilities,
        service_log_path=os.path.devnull)
    browser.set_page_load_timeout(30)
    browser.set_script_timeout(30)

    def fin():
        console_messages = browser.get_log('browser')
        if len(console_messages) > 0:
            print("\n<-- CAPTURED JAVASCRIPT CONSOLE MESSAGES -->")
            for message in console_messages:
                print(message)
            print("<------------------------------------------>")
        browser.save_screenshot(os.path.join(os.path.dirname(__file__), 'selenium.screenshot.png'))
        browser.quit()
    request.addfinalizer(fin)

    return browser


notwindows = pytest.mark.skipif(
    sys.platform == 'win32',
    reason="Assignment List extension is not available on windows"
)
