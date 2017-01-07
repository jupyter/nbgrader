import pytest

from .base import BaseTestFormgrade
from .conftest import jupyterhub


@jupyterhub
@pytest.mark.usefixtures("all_formgraders")
class TestInvalidGrader(BaseTestFormgrade):

    def test_start(self):
        # This is just a fake test, since starting up the browser and formgrader
        # can take a little while. So if anything goes wrong there, this test
        # will fail, rather than having it fail on some other test.
        pass

    def test_invalid_login(self):
        if self.manager.jupyterhub is None:
            pytest.skip("JupyterHub is not running")

        self._get(self.manager.base_formgrade_url)
        self._wait_for_element("username_input")
        next_url = self.formgrade_url().replace(self.manager.base_url, "")
        self._check_url("{}/hub/login?next={}".format(self.manager.base_url, next_url))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("baz")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("")
        self._wait_for_element("error-403")

        # logout
        self._get("{}/hub/logout".format(self.manager.base_url))
        self._wait_for_element("username_input")
