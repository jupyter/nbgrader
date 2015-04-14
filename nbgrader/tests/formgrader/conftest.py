import pytest
import os
import shutil
import tempfile
import sys

from nbgrader.api import Gradebook
from selenium import webdriver

from .. import run_command
from . import manager


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
def gradebook(request, tempdir):
    # create a "class files" directory
    origdir = os.getcwd()
    os.mkdir("class_files")
    os.chdir("class_files")

    # copy files from the user guide
    shutil.copytree(os.path.join(os.path.dirname(__file__), "files", "source"), "source")
    shutil.copytree(os.path.join(os.path.dirname(__file__), "files", "submitted"), "submitted")

    # create the gradebook
    gb = Gradebook("sqlite:///gradebook.db")
    gb.add_assignment("Problem Set 1")
    gb.add_student("Bitdiddle", first_name="Ben", last_name="B")
    gb.add_student("Hacker", first_name="Alyssa", last_name="H")
    gb.add_student("Reasoner", first_name="Louis", last_name="R")

    # run nbgrader assign
    run_command(
        'nbgrader assign "Problem Set 1" '
        '--IncludeHeaderFooter.header=source/header.ipynb')

    # run the autograder
    run_command('nbgrader autograde "Problem Set 1"')

    def fin():
        os.chdir(origdir)
        shutil.rmtree("class_files")
    request.addfinalizer(fin)

    return gb


# skip if less than Python 3
minversion = pytest.mark.skipif(
    sys.version_info[0] < 3,
    reason="JupyterHub tests require Python 3")

# parameterize the formgrader to run under all managers
@pytest.fixture(
    scope="class",
    params=[minversion(x) if x.startswith("Hub") else x for x in manager.__all__]
)
def formgrader(request, gradebook, tempdir):
    man = getattr(manager, request.param)(tempdir)
    man.start()

    browser = webdriver.PhantomJS()

    request.cls.manager = man
    request.cls.gradebook = gradebook
    request.cls.browser = browser

    def fin():
        browser.save_screenshot(os.path.join(os.path.dirname(__file__), 'selenium.screenshot.png'))
        browser.quit()
        man.stop()
    request.addfinalizer(fin)
