import pytest
import tempfile
import os
import shutil
import subprocess as sp
import logging
import time

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from textwrap import dedent

from nbformat import write as write_nb
from nbformat.v4 import new_notebook

from .. import run_python_module, copy_coverage_files
from ...api import Gradebook

@pytest.fixture(scope="module")
def tempdir(request):
    tempdir = tempfile.mkdtemp()
    origdir = os.getcwd()
    os.chdir(tempdir)

    def fin():
        os.chdir(origdir)
        shutil.rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="module")
def jupyter_config_dir(request):
    jupyter_config_dir = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(jupyter_config_dir)
    request.addfinalizer(fin)

    return jupyter_config_dir

@pytest.fixture(scope="module")
def jupyter_data_dir(request):
    jupyter_data_dir = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(jupyter_data_dir)
    request.addfinalizer(fin)

    return jupyter_data_dir


@pytest.fixture(scope="module")
def exchange(request):
    exchange = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(exchange)
    request.addfinalizer(fin)

    return exchange


@pytest.fixture(scope="module")
def cache(request):
    cache = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(cache)
    request.addfinalizer(fin)

    return cache


@pytest.fixture(scope="module")
def class_files(request, tempdir):
    # copy files from the user guide
    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "source", "user_guide", "source")
    shutil.copytree(os.path.join(os.path.dirname(__file__), source_path), "source")

    # create a fake ps1
    os.mkdir(os.path.join("source", "ps1"))
    with open(os.path.join("source", "ps1", "problem 1.ipynb"), "w") as fh:
        write_nb(new_notebook(), fh, 4)

    # create the gradebook
    gb = Gradebook("sqlite:///gradebook.db")
    gb.add_assignment("Problem Set 1")
    gb.add_assignment("ps1")
    gb.add_student("Bitdiddle", first_name="Ben", last_name="B")
    gb.add_student("Hacker", first_name="Alyssa", last_name="H")
    gb.add_student("Reasoner", first_name="Louis", last_name="R")

    return tempdir


@pytest.fixture(scope="module")
def nbserver(request, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    env = os.environ.copy()
    env['JUPYTER_CONFIG_DIR'] = jupyter_config_dir
    env['JUPYTER_DATA_DIR'] = jupyter_data_dir

    nbextension_dir = os.path.join(jupyter_data_dir, "nbextensions")
    run_python_module(["nbgrader", "extension", "install", "--nbextensions", nbextension_dir], env=env)
    run_python_module(["nbgrader", "extension", "activate"], env=env)

    # create nbgrader_config.py file
    with open('nbgrader_config.py', 'w') as fh:
        fh.write(dedent(
            """
            c = get_config()
            c.TransferApp.exchange_directory = '{}'
            c.TransferApp.cache_directory = '{}'
            """.format(exchange, cache)
        ))

    nbserver = sp.Popen([
        sys.executable, "-m", "jupyter", "notebook",
        "--no-browser",
        "--port", "9000"], env=env)

    def fin():
        nbserver.send_signal(15) # SIGTERM
        for i in range(10):
            retcode = nbserver.poll()
            if retcode is not None:
                break
            time.sleep(0.1)
        if retcode is None:
            print("couldn't shutdown notebook server, force killing it")
            nbserver.kill()
        copy_coverage_files()
    request.addfinalizer(fin)

    return nbserver


@pytest.fixture
def browser(request, tempdir, nbserver):
    shutil.copy(os.path.join(os.path.dirname(__file__), "files", "blank.ipynb"), os.path.join(tempdir, "blank.ipynb"))

    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.WARNING)

    capabilities = DesiredCapabilities.PHANTOMJS
    capabilities['loggingPrefs'] = {'browser': 'ALL'}
    browser = webdriver.PhantomJS(desired_capabilities=capabilities)
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


