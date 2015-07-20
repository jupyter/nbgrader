import pytest

from nbgrader.tests.formgrader.base import BaseTestFormgrade

@pytest.mark.js
@pytest.mark.usefixtures("bad_formgrader")
class TestAuthFailures(BaseTestFormgrade):

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_login(self):
        self.browser.get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        next_url = self.formgrade_url().replace("http://localhost:8000", "")
        self._check_url("http://localhost:8000/hub/login?next={}".format(next_url))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("foobar")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("assignments")
        self._wait_for_element("error-500")


@pytest.mark.js
@pytest.mark.usefixtures("all_formgraders")
class TestInvalidGrader(BaseTestFormgrade):

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_invalid_login(self):
        if self.manager.jupyterhub is None:
            return

        self.browser.get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        next_url = self.formgrade_url().replace("http://localhost:8000", "")
        self._check_url("http://localhost:8000/hub/login?next={}".format(next_url))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("baz")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("assignments")
        self._wait_for_element("error-403")
