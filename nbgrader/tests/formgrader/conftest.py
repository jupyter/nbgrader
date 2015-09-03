import pytest
import os
import shutil
import tempfile
import sys
import logging

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from ...api import Gradebook
from ...utils import rmtree
from .. import run_python_module
from . import manager, bad_manager


@pytest.fixture(scope="session")
def tempdir(request):
    tempdir = tempfile.mkdtemp()
    origdir = os.getcwd()
    os.chdir(tempdir)

    def fin():
        os.chdir(origdir)
        rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="session")
def gradebook(request, tempdir):
    # create a "class files" directory
    origdir = os.getcwd()
    os.mkdir("class_files")
    os.chdir("class_files")

    # copy files from the user guide
    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "source", "user_guide", "source")
    submitted_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "source", "user_guide", "submitted")

    shutil.copytree(os.path.join(os.path.dirname(__file__), source_path), "source")
    shutil.copytree(os.path.join(os.path.dirname(__file__), submitted_path), "submitted")

    # create the gradebook
    gb = Gradebook("sqlite:///gradebook.db")
    gb.add_assignment("Problem Set 1")
    gb.add_student("Bitdiddle", first_name="Ben", last_name="B")
    gb.add_student("Hacker", first_name="Alyssa", last_name="H")
    gb.add_student("Reasoner", first_name="Louis", last_name="R")

    # run nbgrader assign
    run_python_module([
        "nbgrader", "assign", "Problem Set 1",
        "--IncludeHeaderFooter.header=source/header.ipynb"
    ])

    # run the autograder
    run_python_module(["nbgrader", "autograde", "Problem Set 1"])

    def fin():
        gb.db.close()
    request.addfinalizer(fin)

    return gb


def _formgrader(request, manager_class, gradebook, tempdir):
    man = manager_class(tempdir)
    man.start()

    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.WARNING)

    capabilities = DesiredCapabilities.PHANTOMJS
    capabilities['loggingPrefs'] = {'browser': 'ALL'}
    capabilities['acceptSslCerts'] = True
    browser = webdriver.PhantomJS(
        service_args=['--ignore-ssl-errors=true'],
        desired_capabilities=capabilities,
        service_log_path=os.path.devnull)
    browser.set_page_load_timeout(10)
    browser.set_script_timeout(10)

    request.cls.manager = man
    request.cls.gradebook = gradebook
    request.cls.browser = browser

    def fin():
        console_messages = browser.get_log('browser')
        if len(console_messages) > 0:
            print("\n<-- CAPTURED JAVASCRIPT CONSOLE MESSAGES -->")
            for message in console_messages:
                print(message)
            print("<------------------------------------------>")
        browser.save_screenshot(os.path.join(os.path.dirname(__file__), 'selenium.screenshot.png'))
        browser.quit()
        man.stop()
    request.addfinalizer(fin)

# Skip if less than Python 3 or if running on Windows
# For some reason stuff isn't properly skipped if I use multiple skipif
# markers, so I'm combining both of them into one here...
skipif = pytest.mark.skipif(
    (sys.version_info[0] < 3) or (sys.platform == 'win32'),
    reason="JupyterHub tests require Python 3 and cannot run on Windows")

formgrader = pytest.mark.formgrader
jupyterhub = lambda x: pytest.mark.jupyterhub(formgrader(skipif(x)))

# parameterize the formgrader to run under all managers
@pytest.fixture(
    scope="class",
    params=[jupyterhub(x) if x.startswith("Hub") else js(x) for x in manager.__all__]
)
def all_formgraders(request, gradebook, tempdir):
    _formgrader(request, getattr(manager, request.param), gradebook, tempdir)

# parameterize the formgrader to run under just the default manager
@pytest.fixture(
    scope="class",
    params=[js("DefaultManager")]
)
def formgrader(request, gradebook, tempdir):
    _formgrader(request, getattr(manager, request.param), gradebook, tempdir)

@pytest.fixture(
    scope="class",
    params=[jupyterhub("BadHubAuthManager")]
)
def bad_formgrader(request, gradebook, tempdir):
    _formgrader(request, getattr(bad_manager, request.param), gradebook, tempdir)
