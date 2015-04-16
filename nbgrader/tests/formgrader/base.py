try:
    from urllib import unquote # Python 2
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin, unquote # Python 3

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseTestFormgrade(object):

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
