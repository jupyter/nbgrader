# -*- coding: utf-8 -*-

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .conftest import notwindows, _make_nbserver, _make_browser, _close_nbserver, _close_browser


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    server = _make_nbserver("course101", port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache)

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
    return WebDriverWait(browser, 10)


def _load_course_list(browser, port, retries=5):
    # go to the correct page
    browser.get("http://localhost:{}/tree".format(port))

    def page_loaded(browser):
        return browser.execute_script(
            'return typeof IPython !== "undefined" && IPython.page !== undefined;')

    # wait for the page to load
    try:
        _wait(browser).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print("Retrying page load...")
            # page timeout, but sometimes this happens, so try refreshing?
            _load_course_list(browser, port, retries=retries - 1)
        else:
            print("Failed to load the page too many times")
            raise

    # wait for the extension to load
    _wait(browser).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#courses")))

    # switch to the courses list
    element = browser.find_element_by_link_text("Courses")
    element.click()

    # make sure courses are visible
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#formgrader_list")))


def _wait_for_list(browser, num_rows):
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#formgrader_list_loading")))
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#formgrader_list_placeholder")))
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#formgrader_list_error")))
    _wait(browser).until(lambda browser: len(browser.find_elements_by_css_selector("#formgrader_list > .list_item")) == num_rows)
    rows = browser.find_elements_by_css_selector("#formgrader_list > .list_item")
    assert len(rows) == num_rows
    return rows


@pytest.mark.nbextensions
@notwindows
def test_show_courses_list(browser, port, tempdir):
    _load_course_list(browser, port)

    # check that there is one local course
    rows = _wait_for_list(browser, 1)
    assert rows[0].text == "course101\nlocal"

    # make sure the url of the course is correct
    link = browser.find_elements_by_css_selector("#formgrader_list > .list_item a")[0]
    url = link.get_attribute("href")
    assert url == "http://localhost:{}/formgrader".format(port)


