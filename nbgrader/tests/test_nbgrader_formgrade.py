import os
import shutil
import tempfile

from .base import TestBase

from nbgrader.api import Gradebook

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
        shutil.copy(os.path.join(user_guide, "grade_example", "nbgrader_formgrade_config.py"), "nbgrader_formgrade_config.py")

        # create the gradebook
        dbpath = "gradebook.db"
        gb = Gradebook("sqlite:///" + dbpath)
        gb.add_assignment("Problem Set 1")
        gb.add_student("Bitdiddle", first_name="Ben", last_name="Bitdiddle")

        # run nbgrader assign
        cls._run_command(
            'nbgrader assign source/*.ipynb '
            '--build-dir=release '
            '--IncludeHeaderFooter.header=header.ipynb '
            '--save-cells '
            '--assignment="Problem Set 1" '
            '--db="sqlite:///{dbpath}"'.format(dbpath=dbpath))

        # run the autograder
        cls._run_command(
            'nbgrader autograde submitted/Bitdiddle/*.ipynb '
            '--build-dir=autograded/Bitdiddle '
            '--student=Bitdiddle '
            '--assignment="Problem Set 1" '
            '--overwrite-cells '
            '--db="sqlite:///{dbpath}"'.format(dbpath=dbpath))

    @classmethod
    def setup(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.ipythondir = tempfile.mkdtemp()
        cls.origdir = os.getcwd()
        os.chdir(cls.tempdir)

        # copy files and setup assignment
        cls._setup_assignment_hierarchy()

        # start the formgrader
        cls.formgrader = cls._start_subprocess('nbgrader formgrade --port=9000')
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def teardown_class(cls):
        cls.browser.quit()
        cls.formgrader.kill()
        cls._copy_coverage_files()

        os.chdir(cls.origdir)
        shutil.rmtree(cls.tempdir)
        shutil.rmtree(cls.ipythondir)

    def test_help(self):
        self._run_command("nbgrader formgrade --help-all")

    def test_load_pages(self):
        self.browser.get("http://localhost:9000")
        self.browser.get("http://localhost:9000/assignments")
        self.browser.get("http://localhost:9000/students")
