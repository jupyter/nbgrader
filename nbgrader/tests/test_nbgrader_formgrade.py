import os
import shutil
import tempfile
import time

from .base import TestBase

from nbgrader.api import Gradebook, MissingEntry
from nose.tools import assert_equal

try:
    from urllib import unquote # Python 2
except ImportError:
    from urllib.parse import unquote # Python 3

from selenium import webdriver

class TestNbgraderFormgrade(TestBase):

    @classmethod
    def _setup_assignment_hierarchy(cls):
        # copy files from the user guide
        user_guide = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "user_guide")
        shutil.copytree(os.path.join(user_guide, "release_example", "teacher"), "source")
        shutil.copytree(os.path.join(user_guide, "grade_example", "submitted"), "submitted")
        shutil.copy(os.path.join(user_guide, "release_example", "header.ipynb"), "header.ipynb")

        # create the gradebook
        cls.gb = Gradebook("sqlite:///gradebook.db")
        cls.gb.add_assignment("Problem Set 1")
        cls.gb.add_student("Bitdiddle", first_name="Ben", last_name="B")
        cls.gb.add_student("Hacker", first_name="Alyssa", last_name="H")
        cls.gb.add_student("Reasoner", first_name="Louis", last_name="R")

        # run nbgrader assign
        cls._run_command(
            'nbgrader assign source/*.ipynb '
            '--build-dir=release '
            '--IncludeHeaderFooter.header=header.ipynb '
            '--save-cells '
            '--assignment="Problem Set 1" '
            '--db="sqlite:///gradebook.db"')

        # run the autograder
        for student_id in os.listdir("submitted"):
            cls._run_command(
                'nbgrader autograde submitted/{student_id}/*.ipynb '
                '--build-dir=autograded/{student_id} '
                '--student={student_id} '
                '--assignment="Problem Set 1" '
                '--overwrite-cells '
                '--db="sqlite:///gradebook.db"'.format(student_id=student_id))

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
            '--FormgradeApp.directory_format="{student_id}/{notebook_id}.ipynb" '
            '--FormgradeApp.nbserver_port=9001 '
            '--port=9000 '
            '--db="sqlite:///gradebook.db"')
        time.sleep(1)
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def teardown_class(cls):
        cls.browser.save_screenshot(os.path.join(cls.origdir, '.selenium.screenshot.png'))
        cls.browser.quit()
        cls.formgrader.terminate()
        time.sleep(1)

        cls._copy_coverage_files()

        os.chdir(cls.origdir)
        shutil.rmtree(cls.tempdir)
        shutil.rmtree(cls.ipythondir)

    def test_help(self):
        self._run_command("nbgrader formgrade --help-all")

    def _check_url(self, url):
        if not url.startswith("http"):
            url = "http://localhost:9000/" + url.strip("/")
        assert_equal(unquote(self.browser.current_url.rstrip("/")), url.strip("/"))

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

    def test_load_assignment_list(self):
        # load the main page and make sure it redirects
        self.browser.get("http://localhost:9000")
        self._check_url("/assignments")
        self._check_breadcrumbs("Assignments")

        # click on the "Problem Set 1" link
        self._click_link("Problem Set 1")
        self._check_url("/assignments/Problem Set 1")

    def test_load_assignment_notebook_list(self):
        self.browser.get("http://localhost:9000/assignments/Problem Set 1")
        self._check_breadcrumbs("Assignments", "Problem Set 1")

        # click the "Assignments" link
        self._click_link("Assignments")
        self._check_url("/assignments")
        self.browser.back()

        # click on the problem link
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            self._click_link(problem.name)
            self._check_url("/assignments/Problem Set 1/{}".format(problem.name))
            self.browser.back()

    def test_load_assignment_notebook_submissions_list(self):
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            self.browser.get("http://localhost:9000/assignments/Problem Set 1/{}".format(problem.name))
            self._check_breadcrumbs("Assignments", "Problem Set 1", problem.name)

            # click the "Assignments" link
            self._click_link("Assignments")
            self._check_url("/assignments")
            self.browser.back()

            # click the "Problem Set 1" link
            self._click_link("Problem Set 1")
            self._check_url("/assignments/Problem Set 1")
            self.browser.back()

            submissions = problem.submissions
            submissions.sort(key=lambda x: x.id)
            for i in range(len(submissions)):
                # click on the "Submission #i" link
                self._click_link("Submission #{}".format(i + 1))
                self._check_url("/submissions/{}".format(submissions[i].id))
                self.browser.back()

    def test_load_student_list(self):
        # load the student view
        self.browser.get("http://localhost:9000/students")
        self._check_url("/students")
        self._check_breadcrumbs("Students")

        # click on student
        for student in self.gb.students:
            ## TODO: they should have a link here, even if they haven't submitted anything!
            if len(student.submissions) == 0:
                continue
            self._click_link("{}, {}".format(student.last_name, student.first_name))
            self._check_url("/students/{}".format(student.id))
            self.browser.back()

    def test_load_student_assignment_list(self):
        for student in self.gb.students:
            self.browser.get("http://localhost:9000/students/{}".format(student.id))
            self._check_breadcrumbs("Students", student.id)

            try:
                submission = self.gb.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self._click_link("Problem Set 1")
            self._check_url("/students/{}/Problem Set 1".format(student.id))

    def test_load_student_assignment_submissions_list(self):
        for student in self.gb.students:
            try:
                submission = self.gb.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self.browser.get("http://localhost:9000/students/{}/Problem Set 1".format(student.id))
            self._check_breadcrumbs("Students", student.id, "Problem Set 1")

            for problem in self.gb.find_assignment("Problem Set 1").notebooks:
                self._click_link(problem.name)
                submission = self.gb.find_submission_notebook(problem.name, "Problem Set 1", student.id)
                self._check_url("/submissions/{}".format(submission.id))
                self.browser.back()

    def test_switch_views(self):
        # load the main page
        self.browser.get("http://localhost:9000")

        # click the "Change View" button
        self._click_link("Change View", partial=True)

        # click the "Students" option
        self._click_link("Students")
        self._check_url("/students")

        # click the "Change View" button
        self._click_link("Change View", partial=True)

        # click the "Assignments" option
        self._click_link("Assignments")
        self._check_url("/assignments")

    def test_formgrade_view_breadcrumbs(self):
        for problem in self.gb.find_assignment("Problem Set 1").notebooks:
            submissions = problem.submissions
            submissions.sort(key=lambda x: x.id)

            for i, submission in enumerate(submissions):
                self.browser.get("http://localhost:9000/submissions/{}".format(submission.id))

                # click on the "Assignments" link
                self._click_link("Assignments")
                self._check_url("/assignments")
                self.browser.back()

                # click on the "Problem Set 1" link
                self._check_url("/submissions/{}".format(submission.id))
                self._click_link("Problem Set 1")
                self._check_url("/assignments/Problem Set 1")
                self.browser.back()

                # click on the problem link
                self._check_url("/submissions/{}".format(submission.id))
                self._click_link(problem.name)
                self._check_url("/assignments/Problem Set 1/{}".format(problem.name))
                self.browser.back()

                # check the live notebook link
                self._click_link("Submission #{}".format(i + 1))
                self.browser.switch_to_window(self.browser.window_handles[1])
                self._check_url("http://localhost:9001/notebooks/{}/{}.ipynb".format(submission.student.id, problem.name))
                self.browser.close()
                self.browser.switch_to_window(self.browser.window_handles[0])
