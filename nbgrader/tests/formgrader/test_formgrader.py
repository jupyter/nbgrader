import pytest
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from nbgrader.tests.formgrader.base import BaseTestFormgrade


@pytest.mark.usefixtures("formgrader")
class TestFormgrader(BaseTestFormgrade):

    def _send_keys_to_body(self, *keys):
        body = self.browser.find_element_by_tag_name("body")
        body.send_keys(*keys)

    def _get_comment_box(self, index):
        return self.browser.find_elements_by_css_selector(".comment")[index]

    def _get_score_box(self, index):
        return self.browser.find_elements_by_css_selector(".score")[index]

    def _save_comment(self, index):
        self._send_keys_to_body(Keys.ESCAPE)
        glyph = self.browser.find_elements_by_css_selector(".comment-saved")[index]
        WebDriverWait(self.browser, 10).until(lambda browser: glyph.is_displayed())
        WebDriverWait(self.browser, 10).until(lambda browser: not glyph.is_displayed())

    def _save_score(self, index):
        self._send_keys_to_body(Keys.ESCAPE)
        glyph = self.browser.find_elements_by_css_selector(".score-saved")[index]
        WebDriverWait(self.browser, 10).until(lambda browser: glyph.is_displayed())
        WebDriverWait(self.browser, 10).until(lambda browser: not glyph.is_displayed())

    def _get_active_element(self):
        return self.browser.execute_script("return document.activeElement;")

    def _load_formgrade(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        self._load_gradebook_page("assignments/Problem Set 1/Problem 1")
        self._click_link("Submission #1")
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        # wait for grades and comments to be loaded
        def grades_and_comments_loaded(browser):
            return browser.execute_script("return grades_loaded && comments_loaded;")
        WebDriverWait(self.browser, 10).until(grades_and_comments_loaded)

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
        self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_RIGHT)
        self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

        # Move to the next submission (should return to notebook list)
        self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_RIGHT)
        self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

        # Go back
        self.browser.back()
        self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

        # Move to the previous submission
        self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_LEFT)
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        # Move to the previous submission (should return to the notebook list)
        self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_LEFT)
        self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

        # Go back
        self.browser.back()
        self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        if submissions[0].failed_tests:
            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            # Go to the other notebook
            self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            # Go to the previous failed submission
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

        else:
            # Go to the next failed submission
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[0].id))

            # Go to the other notebook
            self._send_keys_to_body(Keys.SHIFT, Keys.ARROW_RIGHT)
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_RIGHT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_notebook_page("submissions/{}".format(submissions[1].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, Keys.ARROW_LEFT)
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

    def test_tabbing(self):
        self._load_formgrade()

        # check that the first comment box is selected
        assert self._get_active_element() == self._get_comment_box(0)

        # tab to the next and check that the first points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(0)

        # tab to the next and check that the second points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(1)

        # tab to the next and check that the second comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(1)

        # tab to the next and check that the third points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(2)

        # tab to the next and check that the fourth points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(3)

        # tab to the next and check that the fifth points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(4)

        # tab to the next and check that the third comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(2)

        # tab to the next and check that the first comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(0)

    @pytest.mark.parametrize("index", range(3))
    def test_save_comment(self, index):
        self._load_formgrade()

        elem = self._get_comment_box(index)
        if elem.get_attribute("value") != "":
            elem.click()
            elem.clear()
            self._save_comment(index)

            self._load_formgrade()
            elem = self._get_comment_box(index)
            assert elem.get_attribute("value") == ""

        elem.click()
        elem.send_keys("this comment has index {}".format(index))
        elem.send_keys(Keys.ENTER)
        elem.send_keys("blah blah blah")
        self._save_comment(index)

        self._load_formgrade()
        elem = self._get_comment_box(index)
        assert elem.get_attribute("value") == "this comment has index {}\nblah blah blah".format(index)

    @pytest.mark.parametrize("index", range(5))
    def test_save_score(self, index):
        self._load_formgrade()

        elem = self._get_score_box(index)
        if elem.get_attribute("value") != "":
            elem.click()
            elem.clear()
            self._save_score(index)

            self._load_formgrade()
            elem = self._get_score_box(index)
            assert elem.get_attribute("value") == ""

        elem.click()
        elem.send_keys("{}".format((index + 1) / 10.0))
        self._save_score(index)

        self._load_formgrade()
        elem = self._get_score_box(index)
        assert elem.get_attribute("value") == "{}".format((index + 1) / 10.0)
