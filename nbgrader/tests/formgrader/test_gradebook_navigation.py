import pytest

from six.moves.urllib.parse import quote

from ...api import MissingEntry
from .base import BaseTestFormgrade


@pytest.mark.formgrader
@pytest.mark.usefixtures("all_formgraders")
class TestGradebook(BaseTestFormgrade):

    def _click_element(self, name):
        self.browser.find_element_by_css_selector(name).click()

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_login(self):
        if self.manager.jupyterhub is None:
            pytest.skip("JupyterHub is not running")

        self._get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        next_url = self.formgrade_url().replace(self.manager.base_url, "")
        self._check_url("{}/hub/login?next={}".format(self.manager.base_url, next_url))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("foobar")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("")

    def test_load_assignment_list(self):
        # load the main page and make sure it is the Assignments page
        self._get(self.formgrade_url())
        self._wait_for_gradebook_page("")
        self._check_breadcrumbs("Assignments")

        # load the assignments page
        self._load_gradebook_page("assignments")
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
                self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[i].id))
                self.browser.back()

    def test_assignment_notebook_submissions_show_hide_names(self):
        problem = self.gradebook.find_assignment("Problem Set 1").notebooks[0]
        self._load_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)
        submission = submissions[0]

        top_elem = self.browser.find_element_by_css_selector("#submission-1")
        col1, col2 = top_elem.find_elements_by_css_selector("td")[:2]
        hidden = col1.find_element_by_css_selector(".glyphicon.name-hidden")
        shown = col1.find_element_by_css_selector(".glyphicon.name-shown")

        # check that the name is hidden
        assert col2.text == "Submission #1"
        assert not shown.is_displayed()
        assert hidden.is_displayed()

        # click the show icon
        hidden.click()

        # check that the name is shown
        assert col2.text == "{}, {}".format(submission.student.last_name, submission.student.first_name)
        assert shown.is_displayed()
        assert not hidden.is_displayed()

        # click the hide icon
        shown.click()

        # check that the name is hidden
        assert col2.text == "Submission #1"
        assert not shown.is_displayed()
        assert hidden.is_displayed()

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
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))
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
                self._get(self.formgrade_url("submissions/{}".format(submission.id)))
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

                # click on the "Assignments" link
                self._click_link("Assignments")
                self._wait_for_gradebook_page("assignments")

                # go back
                self.browser.back()
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

                # click on the "Problem Set 1" link
                self._click_link("Problem Set 1")
                self._wait_for_gradebook_page("assignments/Problem Set 1")

                # go back
                self.browser.back()
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

                # click on the problem link
                self._click_link(problem.name)
                self._wait_for_gradebook_page("assignments/Problem Set 1/{}".format(problem.name))

                # go back
                self.browser.back()
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

    def test_load_live_notebook(self):
        for problem in self.gradebook.find_assignment("Problem Set 1").notebooks:
            submissions = problem.submissions
            submissions.sort(key=lambda x: x.id)

            for i, submission in enumerate(submissions):
                self._get(self.formgrade_url("submissions/{}".format(submission.id)))
                self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

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
            self._get(self.formgrade_url("submissions/{}".format(submission.id)))
            self._wait_for_formgrader("submissions/{}/?index=0".format(submission.id))

            images = self.browser.find_elements_by_tag_name("img")
            for image in images:
                # check that the image is loaded, and that it has a width
                assert self.browser.execute_script("return arguments[0].complete", image)
                assert self.browser.execute_script("return arguments[0].naturalWidth", image) > 0

    def test_next_prev_assignments(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        # test navigating both with the arrow keys and with clicking the
        # next/previous links
        next_functions = [
            (self._click_element, ".next a")
        ]
        prev_functions = [
            (self._click_element, ".previous a")
        ]

        for n, p in zip(next_functions, prev_functions):
            # first element is the function, the other elements are the arguments
            # to that function
            next_function = lambda: n[0](*n[1:])
            prev_function = lambda: p[0](*p[1:])

            # Load the first submission
            self._get(self.formgrade_url("submissions/{}".format(submissions[0].id)))
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Move to the next submission
            next_function()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Move to the next submission (should return to notebook list)
            next_function()
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Move to the previous submission
            prev_function()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Move to the previous submission (should return to the notebook list)
            prev_function()
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

    def test_logout(self):
        """Make sure after we've logged out we can't access any of the formgrader pages."""
        if self.manager.jupyterhub is None:
            pytest.skip("JupyterHub is not running")

        # logout and wait for the login page to appear
        self._get("{}/hub".format(self.manager.base_url))
        self._wait_for_element("logout")
        self._wait_for_visibility_of_element("logout")
        element = self.browser.find_element_by_id("logout")
        element.click()
        self._wait_for_element("username_input")

        # try going to a formgrader page
        self._get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        next_url = self.formgrade_url().replace(self.manager.base_url, "")
        self._check_url("{}/hub/login?next={}".format(self.manager.base_url, next_url))

        # try going to a live notebook page
        problem = self.gradebook.find_assignment("Problem Set 1").notebooks[0]
        submission = sorted(problem.submissions, key=lambda x: x.id)[0]
        url = self.notebook_url("autograded/{}/Problem Set 1/{}.ipynb".format(submission.student.id, problem.name))
        self._get(url)
        self._wait_for_element("username_input")
        next_url = url.replace(self.manager.base_url, "/hub")
        self._check_url("{}/hub/login?next={}".format(self.manager.base_url, quote(next_url)))

