import pytest

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from nbgrader.api import MissingEntry
from nbgrader.tests.formgrader.base import BaseTestFormgrade


@pytest.mark.usefixtures("formgrader")
class TestGradebook(BaseTestFormgrade):

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
