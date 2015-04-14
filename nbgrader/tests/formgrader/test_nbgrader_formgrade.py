import pytest

try:
    from urllib import unquote # Python 2
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin, unquote # Python 3

from nbgrader.api import MissingEntry

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .. import run_command


def test_help():
    run_command("nbgrader formgrade --help-all")


@pytest.mark.usefixtures("formgrader")
class TestNbgraderFormgrade(object):

    def formgrade_url(self, url=""):
        return urljoin(self.manager.base_formgrade_url, url).rstrip("/")

    def notebook_url(self, url=""):
        return urljoin(self.manager.base_notebook_url, url).rstrip("/")

    def _check_url(self, url):
        if not url.startswith("http"):
            url = self.formgrade_url(url)
        assert unquote(self.browser.current_url.rstrip("/")) == url

    def _check_breadcrumbs(self, *breadcrumbs):
        # check that breadcrumbs are correct
        elements = self.browser.find_elements_by_css_selector("ul.breadcrumb li")
        assert tuple([e.text for e in elements]) == breadcrumbs

        # check that the active breadcrumb is correct
        element = self.browser.find_element_by_css_selector("ul.breadcrumb li.active")
        assert element.text == breadcrumbs[-1]

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

    def _send_keys_to_active_element(self, *keys):
        element = self.browser.execute_script("return document.activeElement")
        element.send_keys(*keys)

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_login(self):
        if self.manager.jupyterhub is None:
            return

        self.browser.get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        self._check_url("http://localhost:8000/hub/login?next={}".format(self.formgrade_url()))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("foobar")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("assignments")

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
        for problem in self.gradebook.find_assignment("Problem Set 1").notebooks:
            self._click_link(problem.name)
            self._wait_for_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))
            self.browser.back()

    def test_load_assignment_notebook_submissions_list(self):
        for problem in self.gradebook.find_assignment("Problem Set 1").notebooks:
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
        for student in self.gradebook.students:
            ## TODO: they should have a link here, even if they haven't submitted anything!
            if len(student.submissions) == 0:
                continue
            self._click_link("{}, {}".format(student.last_name, student.first_name))
            self._wait_for_gradebook_page("students/{}".format(student.id))
            self.browser.back()

    def test_load_student_assignment_list(self):
        for student in self.gradebook.students:
            self._load_gradebook_page("students/{}".format(student.id))
            self._check_breadcrumbs("Students", student.id)

            try:
                self.gradebook.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self._click_link("Problem Set 1")
            self._wait_for_gradebook_page("students/{}/Problem Set 1".format(student.id))

    def test_load_student_assignment_submissions_list(self):
        for student in self.gradebook.students:
            try:
                submission = self.gradebook.find_submission("Problem Set 1", student.id)
            except MissingEntry:
                ## TODO: make sure link doesn't exist
                continue

            self._load_gradebook_page("students/{}/Problem Set 1".format(student.id))
            self._check_breadcrumbs("Students", student.id, "Problem Set 1")

            for problem in self.gradebook.find_assignment("Problem Set 1").notebooks:
                submission = self.gradebook.find_submission_notebook(problem.name, "Problem Set 1", student.id)
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
        for problem in self.gradebook.find_assignment("Problem Set 1").notebooks:
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

    def test_formgrade_images(self):
        submissions = self.gradebook.find_notebook("Problem 1", "Problem Set 1").submissions
        submissions.sort(key=lambda x: x.id)

        for submission in submissions:
            self.browser.get(self.formgrade_url("submissions/{}".format(submission.id)))
            self._wait_for_notebook_page("submissions/{}".format(submission.id))

            images = self.browser.find_elements_by_tag_name("img")
            for image in images:
                # check that the image is loaded, and that it has a width
                assert self.browser.execute_script("return arguments[0].complete", image)
                assert self.browser.execute_script("return arguments[0].naturalWidth", image) > 0

    def test_next_prev_assignments(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        # verify that we have the right number of submissions, and that one
        # failed tests and the other didn't
        assert len(submissions) == 2
        if submissions[0].failed_tests:
            assert not submissions[1].failed_tests
        else:
            assert submissions[1].failed_tests

        # Load the first submission
        self.browser.get(self.formgrade_url("submissions/{}".format(submissions[0].id)))
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        # Move to the next submission
        self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_RIGHT)
        self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

        # Move to the next submission (should return to notebook list)
        self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_RIGHT)
        self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

        # Go back
        self.browser.back()
        self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

        # Move to the previous submission
        self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_LEFT)
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        # Move to the previous submission (should return to the notebook list)
        self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_LEFT)
        self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

        # Go back
        self.browser.back()
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        if submissions[0].failed_tests:
            print("Go to the next failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            print("Go to the previous failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            print("Go to the other notebook")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            print("Go to the next failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            print("Go to the previous failed submission")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        else:
            print("Go to the next failed submission")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            print("Go to the previous failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            print("Go to the other notebook")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            print("Go to the next failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            print("Go back")
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            print("Go to the previous failed submission (should return to the notebook list)")
            self._send_keys_to_active_element(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")
