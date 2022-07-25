import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException

from .conftest import _make_nbserver, _make_browser, _close_nbserver, _close_browser


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    server = _make_nbserver("", port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache)

    def fin():
        _close_nbserver(server)

    request.addfinalizer(fin)

    return server


@pytest.fixture(scope="module")
def browser(request, tempdir, nbserver):
    browser = _make_browser(tempdir)

    def fin():
        _close_browser(browser)

    request.addfinalizer(fin)

    return browser


def _wait(browser):
    return WebDriverWait(browser, 30)


def _load_notebook(browser, port, notebook, retries=5):
    # go to the correct page
    url = "http://localhost:{}/notebooks/{}.ipynb".format(port, notebook)
    browser.get(url)

    alert = ''
    for _ in range(5):
        if alert is None:
            break

        try:
            alert = browser.switch_to.alert
        except NoAlertPresentException:
            alert = None
        else:
            print("Warning: dismissing unexpected alert ({})".format(alert.text))
            alert.accept()

    def page_loaded(browser):
        return browser.execute_script(
            """
            return (typeof Jupyter !== "undefined" &&
                    Jupyter.page !== undefined &&
                    Jupyter.notebook !== undefined &&
                    $("#notebook_name").text() === "{}");
            """.format(notebook))

    # wait for the page to load
    try:
        _wait(browser).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print("Retrying page load...")
            # page timeout, but sometimes this happens, so try refreshing?
            _load_notebook(browser, port, retries=retries - 1, notebook=notebook)
        else:
            print("Failed to load the page too many times")
            raise


@pytest.mark.nbextensions
def test_validate_ok(browser, port):
    _load_notebook(browser, port, "limited_test_cell_height")

    # check that it succeeded
    element = browser.find_element_by_css_selector("CodeMirror cm-s-ipython")
    style = element.get_attribute("style")
    assert style == 'height: 100px;'
