import pytest

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .base import BaseTestFormgrade


@pytest.mark.formgrader
@pytest.mark.usefixtures("formgrader")
class TestFormgraderJS(BaseTestFormgrade):

    def _send_keys_to_body(self, *keys):
        body = self.browser.find_element_by_tag_name("body")
        body.send_keys(*keys)

    def _click_element(self, name):
        self.browser.find_element_by_css_selector(name).click()

    def _get_next_arrow(self):
        return self.browser.find_element_by_css_selector(".next a")

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

    def _get_needs_manual_grade(self, name):
        return self.browser.execute_script(
            'return formgrader.grades.findWhere({name: "%s"}).get("needs_manual_grade");' % name)

    def _flag(self):
        self._send_keys_to_body(Keys.SHIFT, Keys.CONTROL, "f")
        message = self.browser.find_element_by_id("statusmessage")
        WebDriverWait(self.browser, 10).until(lambda browser: message.is_displayed())
        WebDriverWait(self.browser, 10).until(lambda browser: not message.is_displayed())
        return self.browser.execute_script("return $('#statusmessage').text();")

    def _get_active_element(self):
        return self.browser.execute_script("return document.activeElement;")

    def _get_index(self):
        return self.browser.execute_script("return formgrader.getIndex(document.activeElement);")

    def _load_formgrade(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        self._load_gradebook_page("assignments/Problem Set 1/Problem 1")
        self._click_link("Submission #1")
        self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_next_prev_assignments(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        # test navigating both with the arrow keys and with clicking the
        # next/previous links
        next_functions = [
            (self._send_keys_to_body, Keys.CONTROL, "."),
            (self._click_element, ".next a")
        ]
        prev_functions = [
            (self._send_keys_to_body, Keys.CONTROL, ","),
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

    def test_next_prev_failed_assignments(self):
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
        self._get(self.formgrade_url("submissions/{}".format(submissions[0].id)))
        self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

        if submissions[0].failed_tests:
            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ".")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ",")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Go to the other notebook
            self._send_keys_to_body(Keys.CONTROL, ".")
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ".")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Go to the previous failed submission
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ",")
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

        else:
            # Go to the next failed submission
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ".")
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ",")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

            # Go to the other notebook
            self._send_keys_to_body(Keys.CONTROL, ".")
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Go to the next failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ".")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

            # Go back
            self.browser.back()
            self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[1].id))

            # Go to the previous failed submission (should return to the notebook list)
            self._send_keys_to_body(Keys.CONTROL, Keys.SHIFT, ",")
            self._wait_for_gradebook_page("assignments/Problem Set 1/Problem 1")

    def test_tabbing(self):
        self._load_formgrade()

        # check that the next arrow is selected
        assert self._get_active_element() == self._get_next_arrow()
        assert self._get_index() == 0

        # check that the first comment box is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(0)
        assert self._get_index() == 1

        # tab to the next and check that the first points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(0)
        assert self._get_index() == 2

        # tab to the next and check that the second points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(1)
        assert self._get_index() == 3

        # tab to the next and check that the second comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(1)
        assert self._get_index() == 4

        # tab to the next and check that the third points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(2)
        assert self._get_index() == 5

        # tab to the next and check that the fourth points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(3)
        assert self._get_index() == 6

        # tab to the next and check that the fifth points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(4)
        assert self._get_index() == 7

        # tab to the next and check that the third comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(2)
        assert self._get_index() == 8

        # tab to the next and check that the sixth points is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_score_box(5)
        assert self._get_index() == 9

        # tab to the next and check that the fourth comment is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_comment_box(3)
        assert self._get_index() == 10

        # tab to the next and check that the next arrow is selected
        self._send_keys_to_body(Keys.TAB)
        assert self._get_active_element() == self._get_next_arrow()
        assert self._get_index() == 0

    @pytest.mark.parametrize("index", range(4))
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

    @pytest.mark.parametrize("index", range(6))
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

        # check whether it needs manual grading
        if elem.get_attribute("placeholder") != "":
            assert not self._get_needs_manual_grade(elem.get_attribute("id"))
            assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
        else:
            assert self._get_needs_manual_grade(elem.get_attribute("id"))
            assert "needs_manual_grade" in elem.get_attribute("class").split(" ")

        # set the grade
        elem.click()
        elem.send_keys("{}".format((index + 1) / 10.0))
        self._save_score(index)
        self._load_formgrade()
        elem = self._get_score_box(index)
        assert elem.get_attribute("value") == "{}".format((index + 1) / 10.0)

        # check whether it needs manual grading
        assert not self._get_needs_manual_grade(elem.get_attribute("id"))
        assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")

        # clear the grade
        elem.click()
        elem.clear()
        self._save_score(index)
        self._load_formgrade()
        elem = self._get_score_box(index)
        assert elem.get_attribute("value") == ""

        # check whether it needs manual grading
        if elem.get_attribute("placeholder") != "":
            assert not self._get_needs_manual_grade(elem.get_attribute("id"))
            assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
        else:
            assert self._get_needs_manual_grade(elem.get_attribute("id"))
            assert "needs_manual_grade" in elem.get_attribute("class").split(" ")

    def test_same_part_navigation(self):
        problem = self.gradebook.find_notebook("Problem 1", "Problem Set 1")
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        # Load the first submission
        self._get(self.formgrade_url("submissions/{}".format(submissions[0].id)))
        self._wait_for_formgrader("submissions/{}/?index=0".format(submissions[0].id))

        # Click the second comment box and navigate to the next submission
        self._get_comment_box(1).click()
        self._send_keys_to_body(Keys.CONTROL, ".")
        self._wait_for_formgrader("submissions/{}/?index=4".format(submissions[1].id))
        assert self._get_active_element() == self._get_comment_box(1)

        # Click the third score box and navigate to the previous submission
        self._get_score_box(2).click()
        self._send_keys_to_body(Keys.CONTROL, ",")
        self._wait_for_formgrader("submissions/{}/?index=5".format(submissions[0].id))
        assert self._get_active_element() == self._get_score_box(2)

        # Click the third comment box and navigate to the next submission
        self._get_comment_box(2).click()
        self._send_keys_to_body(Keys.CONTROL, ".")
        self._wait_for_formgrader("submissions/{}/?index=7".format(submissions[1].id))
        assert self._get_active_element() == self._get_score_box(4)

        # Navigate to the previous submission
        self._send_keys_to_body(Keys.CONTROL, ",")
        self._wait_for_formgrader("submissions/{}/?index=7".format(submissions[0].id))
        assert self._get_active_element() == self._get_score_box(4)

    def test_keyboard_help(self):
        self._load_formgrade()

        # show the help dialog
        self._click_element(".help")
        self._wait_for_element("help-dialog")
        WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#help-dialog button.btn-primary")))

        # close it
        self._click_element("#help-dialog button.btn-primary")
        modal_not_present = lambda browser: browser.execute_script("""return $("#help-dialog").length === 0;""")
        WebDriverWait(self.browser, 10).until(modal_not_present)

    def test_flag(self):
        self._load_formgrade()

        # mark as flagged
        assert self._flag() == "Submission flagged"

        # mark as unflagged
        assert self._flag() == "Submission unflagged"

        # mark as flagged
        assert self._flag() == "Submission flagged"

        # mark as unflagged
        assert self._flag() == "Submission unflagged"
