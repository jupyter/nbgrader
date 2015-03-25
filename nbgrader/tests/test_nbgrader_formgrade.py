import os
import shutil
import tempfile
import time

from .base import TestBase

from nbgrader.api import Gradebook, MissingEntry
from nose.tools import assert_equal
from textwrap import dedent

try:
    from urllib import unquote # Python 2
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin, unquote # Python 3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestNbgraderFormgrade(TestBase):

    base_formgrade_url = "http://localhost:9000/"
    base_notebook_url = "http://localhost:9001/notebooks/"

    def formgrade_url(self, url=""):
        return urljoin(self.base_formgrade_url, url).rstrip("/")

    def notebook_url(self, url=""):
        return urljoin(self.base_notebook_url, url).rstrip("/")

    @classmethod
    def _setup_assignment_hierarchy(cls):
        # create a "class files" directory
        os.mkdir("class_files")
        os.chdir("class_files")

        # copy files from the user guide
        user_guide = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "user_guide", "example")
        shutil.copytree(os.path.join(user_guide, "source"), "source")
        shutil.copytree(os.path.join(user_guide, "submitted"), "submitted")

        # create the gradebook
        cls.gb = Gradebook("sqlite:///gradebook.db")
        cls.gb.add_assignment("Problem Set 1")
        cls.gb.add_student("Bitdiddle", first_name="Ben", last_name="B")
        cls.gb.add_student("Hacker", first_name="Alyssa", last_name="H")
        cls.gb.add_student("Reasoner", first_name="Louis", last_name="R")

        # run nbgrader assign
        cls._run_command(
            'nbgrader assign "Problem Set 1" '
            '--IncludeHeaderFooter.header=source/header.ipynb')

        # run the autograder
        cls._run_command('nbgrader autograde "Problem Set 1"')

    @classmethod
    def _setup_formgrade_config(cls):
        # create config file
        with open("nbgrader_config.py", "w") as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.NoAuth.nbserver_port = 9001
                c.FormgradeApp.port = 9000
                """
            ))

    @classmethod
    def _start_formgrader(cls):
        cls.formgrader = cls._start_subprocess(
            ["nbgrader", "formgrade"],
            shell=False,
            stdout=None,
            stderr=None)

        time.sleep(1)

    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.origdir = os.getcwd()
        os.chdir(cls.tempdir)

        # copy files and setup assignment
        cls._setup_assignment_hierarchy()

        # create the config file
        cls._setup_formgrade_config()

        # start the formgrader
        cls._start_formgrader()

        # start the browser
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def _stop_formgrader(cls):
        cls.formgrader.terminate()

        # wait for the formgrader to shut down
        for i in range(10):
            retcode = cls.formgrader.poll()
            if retcode is not None:
                break
            time.sleep(0.1)

        # not shutdown, force kill it
        if retcode is None:
            cls.formgrader.kill()

    @classmethod
    def teardown_class(cls):
        cls.browser.save_screenshot(os.path.join(cls.origdir, '.selenium.screenshot.png'))
        cls.browser.quit()
        cls._stop_formgrader()

        cls._copy_coverage_files()

        os.chdir(cls.origdir)
        shutil.rmtree(cls.tempdir)

    def test_help(self):
        self._run_command("nbgrader formgrade --help-all")

    def _check_url(self, url):
        if not url.startswith("http"):
            url = self.formgrade_url(url)
        assert_equal(unquote(self.browser.current_url.rstrip("/")), url)

    def _check_breadcrumbs(self, *breadcrumbs):
        # check that breadcrumbs are correct
        elements = self.browser.find_elements_by_css_selector("ul.breadcrumb li")
        assert_equal(tuple([e.text for e in elements]), breadcrumbs)

        # check that the active breadcrumb is correct
        element = self.browser.find_element_by_css_selector("ul.breadcrumb li.active")
        assert_equal(element.text, breadcrumbs[-1])

    def _click_link(self, link_text, partial=False):
        if partial:
            element = self.browser.find_element_by_partial_link_text(link_text)
        else:
            element = self.browser.find_element_by_link_text(link_text)
        element.click()

    def _wait_for_element(self, element_id, time=10):
        return WebDriverWait(self.browser, time).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

    def _wait_for_gradebook_page(self, url):
        self._wait_for_element("gradebook")
        self._check_url(url)

    def _load_gradebook_page(self, url):
        self.browser.get(self.formgrade_url(url))
        self._wait_for_gradebook_page(url)

    def _wait_for_notebook_page(self, url):
        self._wait_for_element("notebook-container")
        self._check_url(url)

    def test_load_assignment_list(self):
        # load the main page and make sure it redirects
        self.browser.get(self.formgrade_url())
        self._wait_for_gradebook_page("assignments")
        self._check_breadcrumbs("Assignments")

        # click on the "Problem Set 1" link
        self._click_link("Problem Set 1")
        self._wait_for_gradebook_page("assignments/Problem Set 1")

    def test_load_assignment_notebook_list(self):
        self._load_gradebook_page("assignments/Problem Set 1")
        self._check_breadcrumbs("Assignments", "Problem Set 1")

        # click the "Assignments" link
        self._click_link("Assignments")
        self._wait_for_gradebook_page("assignments")
        self.browser.back()

        # click on the problem link
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            self._click_link(problem.name)
            self._wait_for_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))
            self.browser.back()

    def test_load_assignment_notebook_submissions_list(self):
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            self._load_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))
            self._check_breadcrumbs("Assignments", "Problem Set 1", problem.name)

            # click the "Assignments" link
            self._click_link("Assignments")
            self._wait_for_gradebook_page("assignments")
            self.browser.back()

            # click the "Problem Set 1" link
            self._click_link("Problem Set 1")
            self._wait_for_gradebook_page("assignments/Problem Set 1")
            self.browser.back()

            submissions = problem.submissions
            submissions.sort(key=lambda x: x.id)
            for i in range(len(submissions)):
                # click on the "Submission #i" link
                self._click_link("Submission #{}".format(i + 1))
                self._wait_for_notebook_page("submissions/{}".format(submissions[i].id))
                self.browser.back()

    def test_load_student_list(self):
        # load the student view
        self._load_gradebook_page("students")
        self._check_breadcrumbs("Students")

        # click on student
        for student in self.gb.students:
            ## TODO: they should have a link here, even if they haven't submitted anything!
            if len(student.submissions) == 0:
                continue
            self._click_link("{}, {}".format(student.last_name, student.first_name))
            self._wait_for_gradebook_page("students/{}".format(student.id))
            self.browser.back()

    def test_load_student_assignment_list(self):
        for student in self.gb.students:
            self._load_gradebook_page("students/{}".format(student.id))
            self._check_breadcrumbs("Students", student.id)

            try:
                submission = self.gb.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self._click_link("Problem Set 1")
            self._wait_for_gradebook_page("students/{}/Problem Set 1".format(student.id))

    def test_load_student_assignment_submissions_list(self):
        for student in self.gb.students:
            try:
                submission = self.gb.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self._load_gradebook_page("students/{}/Problem Set 1".format(student.id))
            self._check_breadcrumbs("Students", student.id, "Problem Set 1")

            for problem in self.gb.find_assignment("Problem Set 1").notebooks:
                submission = self.gb.find_submission_notebook(problem.name, "Problem Set 1", student.id)
                self._click_link(problem.name)
                self._wait_for_notebook_page("submissions/{}".format(submission.id))
                self.browser.back()
                self._wait_for_gradebook_page("students/{}/Problem Set 1".format(student.id))

    def test_switch_views(self):
        # load the main page
        self._load_gradebook_page("assignments")

        # click the "Change View" button
        self._click_link("Change View", partial=True)

        # click the "Students" option
        self._click_link("Students")
        self._wait_for_gradebook_page("students")

        # click the "Change View" button
        self._click_link("Change View", partial=True)

        # click the "Assignments" option
        self._click_link("Assignments")
        self._wait_for_gradebook_page("assignments")

    def test_formgrade_view_breadcrumbs(self):
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            submissions = problem.submissions
            submissions.sort(key=lambda x: x.id)

            for i, submission in enumerate(submissions):
                self.browser.get(self.formgrade_url("submissions/{}".format(submission.id)))
                self._wait_for_notebook_page("submissions/{}".format(submission.id))

                # click on the "Assignments" link
                self._click_link("Assignments")
                self._wait_for_gradebook_page("assignments")

                # go back
                self.browser.back()
                self._wait_for_notebook_page("submissions/{}".format(submission.id))

                # click on the "Problem Set 1" link
                self._click_link("Problem Set 1")
                self._wait_for_gradebook_page("assignments/Problem Set 1")

                # go back
                self.browser.back()
                self._wait_for_notebook_page("submissions/{}".format(submission.id))

                # click on the problem link
                self._click_link(problem.name)
                self._wait_for_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))

                # go back
                self.browser.back()
                self._wait_for_notebook_page("submissions/{}".format(submission.id))

                # check the live notebook link
                self._click_link("Submission #{}".format(i + 1))
                self.browser.switch_to_window(self.browser.window_handles[1])
                self._wait_for_notebook_page(self.notebook_url("autograded/{}/Problem Set 1/{}.ipynb".format(submission.student.id, problem.name)))
                self.browser.close()
                self.browser.switch_to_window(self.browser.window_handles[0])
