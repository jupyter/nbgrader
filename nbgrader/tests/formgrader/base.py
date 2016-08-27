from six.moves.urllib.parse import urljoin, unquote
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class BaseTestFormgrade(object):
    """Do NOT add any test cases to this base class. This class is for helper
    functions ONLY. If you add test cases, it will break the tests in
    test_formgrader.py and/or test_gradebook.py!

    """

    def formgrade_url(self, url=""):
        return urljoin(self.manager.base_formgrade_url, url).rstrip("/")

    def notebook_url(self, url=""):
        return urljoin(self.manager.base_notebook_url, url).rstrip("/")

    def _check_url(self, url):
        if not url.startswith("http"):
            url = self.formgrade_url(url)
        assert unquote(self.browser.current_url).rstrip("/") == url

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

    def _wait_for_visibility_of_element(self, element_id, time=10):
        return WebDriverWait(self.browser, time).until(
            EC.visibility_of_element_located((By.ID, element_id))
        )

    def _wait_for_gradebook_page(self, url):
        self._wait_for_element("gradebook")
        self._check_url(url)

    def _get(self, url, retries=5):
        try:
            self.browser.get(url)
        except TimeoutException:
            if retries == 0:
                raise
            else:
                print("Failed to load '{}', trying again...".format(url))
                self._get(url, retries=retries - 1)

    def _load_gradebook_page(self, url):
        self._get(self.formgrade_url(url))
        self._wait_for_gradebook_page(url)

    def _wait_for_notebook_page(self, url):
        self._wait_for_element("notebook-container")
        self._check_url(url)

    def _wait_for_formgrader(self, url, retries=5):
        page_loaded = lambda browser: browser.execute_script(
            """
            if (!(typeof MathJax !== "undefined" && MathJax !== undefined && MathJax.loaded)) {
                return false;
            }

            if (!(typeof formgrader !== "undefined" && formgrader !== undefined)) {
                return false;
            }

            if (!(formgrader.grades !== undefined && formgrader.grades.loaded)) {
                return false;
            }

            if (!(formgrader.comments !== undefined && formgrader.comments.loaded)) {
                return false;
            }

            if (!(typeof autosize !== "undefined" && autosize !== undefined)) {
                return false;
            }

            return true;
            """)
        try:
            self._wait_for_element("notebook-container")
            WebDriverWait(self.browser, 10).until(page_loaded)
        except TimeoutException:
            if retries == 0:
                raise
            else:
                print("Failed to load formgrader (url '{}'), trying again...".format(url))
                self._get(self.browser.current_url)
                self._wait_for_formgrader(url, retries=retries - 1)

        self._check_url(url)
