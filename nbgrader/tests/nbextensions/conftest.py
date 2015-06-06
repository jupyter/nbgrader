import pytest
import tempfile
import os
import shutil
import subprocess as sp
import logging
import time

from copy import copy
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from .. import run_command

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
def ipythondir(request):
    ipythondir = tempfile.mkdtemp()

    # ensure IPython dir exists.
    sp.call(['ipython', 'profile', 'create', '--ipython-dir', ipythondir])

    def fin():
        shutil.rmtree(ipythondir)
    request.addfinalizer(fin)

    return ipythondir


@pytest.fixture(scope="module")
def nbserver(request, tempdir, ipythondir):
    run_command("nbgrader extension install --nbextensions={}".format(os.path.join(ipythondir, "nbextensions")))
    run_command("nbgrader extension activate --ipython-dir={}".format(ipythondir))

    # bug in IPython cannot use --profile-dir
    # that does not set it for everything.
    # still this does not allow to have things that work.
    env = copy(os.environ)
    env['IPYTHONDIR'] = ipythondir

    nbserver = sp.Popen([
        "ipython", "notebook",
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


