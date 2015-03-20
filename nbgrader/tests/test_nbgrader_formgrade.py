import os
import shutil
import tempfile

from .base import TestBase

from nbgrader.api import Gradebook
from nose.tools import assert_equal

try:
    from urllib import unquote # Python 2
except ImportError:
    from urllib.parse import unquote # Python 3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class TestNbgraderFormgrade(TestBase):

    @classmethod
    def _setup_assignment_hierarchy(cls):
        # copy files from the user guide
        os.mkdir("submitted")
        user_guide = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "user_guide")
        shutil.copytree(os.path.join(user_guide, "release_example", "teacher"), "source")
        shutil.copytree(os.path.join(user_guide, "grade_example", "submitted", "Bitdiddle"), "submitted/Bitdiddle")
        shutil.copy(os.path.join(user_guide, "release_example", "header.ipynb"), "header.ipynb")

        # create the gradebook
        gb = Gradebook("sqlite:///gradebook.db")
        gb.add_assignment("Problem Set 1")
        gb.add_student("Bitdiddle", first_name="Ben", last_name="Bitdiddle")

        # run nbgrader assign
        cls._run_command(
            'nbgrader assign source/*.ipynb '
            '--build-dir=release '
            '--IncludeHeaderFooter.header=header.ipynb '
            '--save-cells '
            '--assignment="Problem Set 1" '
            '--db="sqlite:///gradebook.db"')

        # run the autograder
        cls._run_command(
            'nbgrader autograde submitted/Bitdiddle/*.ipynb '
            '--build-dir=autograded/Bitdiddle '
            '--student=Bitdiddle '
            '--assignment="Problem Set 1" '
            '--overwrite-cells '
            '--db="sqlite:///gradebook.db"')

    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.ipythondir = tempfile.mkdtemp()
        cls.origdir = os.getcwd()
        os.chdir(cls.tempdir)

        # copy files and setup assignment
        cls._setup_assignment_hierarchy()

        # start the formgrader
        cls.formgrader = cls._start_subprocess(
            'nbgrader formgrade '
            '--FormgradeApp.base_directory=autograded '
            '--FormgradeApp.directory_structure="{student_id}/{notebook_id}.ipynb" '
            '--port=9000 '
            '--db="sqlite:///gradebook.db"',
            stdout=None, stderr=None)
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def teardown_class(cls):
        cls.browser.save_screenshot(os.path.join(cls.origdir, '.selenium.screenshot.png'))
        cls.browser.quit()
        cls._copy_coverage_files()

        os.chdir(cls.origdir)
        shutil.rmtree(cls.tempdir)
        shutil.rmtree(cls.ipythondir)

    def test_help(self):
        self._run_command("nbgrader formgrade --help-all")

    def _check_url(self, url):
        assert_equal(
            unquote(self.browser.current_url.rstrip("/")), 
            "http://localhost:9000/" + url.strip("/"))

    def _check_breadcrumbs(self, *breadcrumbs):
        # check that breadcrumbs are correct
        elements = self.browser.find_elements_by_css_selector("ul.breadcrumb li")
        assert_equal(tuple([e.text for e in elements]), breadcrumbs)

        # check that the active breadcrumb is correct
        element = self.browser.find_element_by_css_selector("ul.breadcrumb li.active")
        assert_equal(element.text, breadcrumbs[-1])

    def _click_link(self, link_text):
        element = self.browser.find_element_by_link_text(link_text)
        element.click()

    def test_load_assignment_view(self):
        # load the main page and make sure it redirects
        self.browser.get("http://localhost:9000")
        self._check_url("/assignments")
        self._check_breadcrumbs("Assignments")

        # click on the "Problem Set 1" link
        self._click_link("Problem Set 1")
        self._check_url("/assignments/Problem Set 1")
        self._check_breadcrumbs("Assignments", "Problem Set 1")

        # click on the "Problem 1" link
        self._click_link("Problem 1")
        self._check_url("/assignments/Problem Set 1/Problem 1")
        self._check_breadcrumbs("Assignments", "Problem Set 1", "Problem 1")

        # go back and click on the "Problem 2" link
        self.browser.back()
        self._click_link("Problem 2")
        self._check_url("/assignments/Problem Set 1/Problem 2")
        self._check_breadcrumbs("Assignments", "Problem Set 1", "Problem 2")

    def test_load_student_view(self):
        # load the student view
        self.browser.get("http://localhost:9000/students")
        self._check_url("/students")
        self._check_breadcrumbs("Students")

        # click on Bitdiddle
        self._click_link("Bitdiddle, Ben")
        self._check_url("/students/Bitdiddle")
        self._check_breadcrumbs("Students", "Bitdiddle")

        # click on the "Problem Set 1" link
        self._click_link("Problem Set 1")
        self._check_url("/students/Bitdiddle/Problem Set 1")
        self._check_breadcrumbs("Students", "Bitdiddle", "Problem Set 1")
