import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


def _load_notebook(browser, retries=5):
    # go to the correct page
    browser.get("http://localhost:9000/notebooks/blank.ipynb")

    def page_loaded(browser):
        return browser.execute_script(
            'return typeof IPython !== "undefined" && IPython.page !== undefined;')

    # wait for the page to load
    try:
        WebDriverWait(browser, 30).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print("Retrying page load...")
            # page timeout, but sometimes this happens, so try refreshing?
            _load_notebook(browser, retries=retries - 1)
        else:
            print("Failed to load the page too many times")
            raise

    # wait for the celltoolbar menu to appear
    WebDriverWait(browser, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctb_select')))

def _activate_toolbar(browser, name="Create Assignment"):
    # activate the Create Assignment toolbar
    element = browser.find_element_by_css_selector("#ctb_select")
    select = Select(element)
    select.select_by_visible_text(name)


def _select_none(browser, index=0):
    select = Select(browser.find_elements_by_css_selector('.celltoolbar select')[index])
    select.select_by_value('')


def _select_manual(browser, index=0):
    select = Select(browser.find_elements_by_css_selector('.celltoolbar select')[index])
    select.select_by_value('manual')


def _select_solution(browser, index=0):
    select = Select(browser.find_elements_by_css_selector('.celltoolbar select')[index])
    select.select_by_value('solution')


def _select_tests(browser, index=0):
    select = Select(browser.find_elements_by_css_selector('.celltoolbar select')[index])
    select.select_by_value('tests')


def _set_points(browser, points=2, index=0):
    elem = browser.find_elements_by_css_selector(".nbgrader-points-input")[index]
    elem.clear()
    elem.send_keys(points)
    browser.find_elements_by_css_selector(".nbgrader-cell")[index].click()


def _set_id(browser, cell_id="foo", index=0):
    elem = browser.find_elements_by_css_selector(".nbgrader-id-input")[index]
    elem.clear()
    elem.send_keys(cell_id)
    browser.find_elements_by_css_selector(".nbgrader-cell")[index].click()


def _get_metadata(browser):
    return browser.execute_script(
        """
        var cell = IPython.notebook.get_cell(0);
        return cell.metadata.nbgrader;
        """
    )


def _get_total_points(browser):
    element = browser.find_element_by_id("nbgrader-total-points")
    return float(element.get_attribute("value"))


@pytest.mark.js
def test_manual_cell(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the toolbar appeared
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar select")))

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it manually graded
    _select_manual(browser)
    assert _get_metadata(browser)['solution']
    assert _get_metadata(browser)['grade']

    # wait for the points and id fields to appear
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-points")))
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']


@pytest.mark.js
def test_solution_cell(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the toolbar appeared
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar select")))

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it a solution cell
    _select_solution(browser)
    assert _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']

    # wait for the id field to appear
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

    # set the id
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']


@pytest.mark.js
def test_tests_cell(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the toolbar appeared
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar select")))

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it autograder tests
    _select_tests(browser)
    assert not _get_metadata(browser)['solution']
    assert _get_metadata(browser)['grade']

    # wait for the points and id fields to appear
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-points")))
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']


@pytest.mark.js
def test_grade_cell_css(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make it manually graded
    _select_manual(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 0

    # make it a solution
    _select_solution(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 0

    # make it autograder tests
    _select_tests(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 0

    # make it autograder tests
    _select_tests(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 1

    # deactivate the toolbar
    _activate_toolbar(browser, "None")
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 0

    # activate the toolbar
    _activate_toolbar(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 1

    # deactivate the toolbar
    _activate_toolbar(browser, "Edit Metadata")
    elements = browser.find_elements_by_css_selector(".nbgrader-cell")
    assert len(elements) == 0


@pytest.mark.js
def test_tabbing(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make it manually graded
    _select_manual(browser)

    # click the id field
    element = browser.find_element_by_css_selector(".nbgrader-points-input")
    element.click()

    # get the active element
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-points-input" == element.get_attribute("class")

    # press tab and check that the active element is correct
    element.send_keys(Keys.TAB)
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-id-input" == element.get_attribute("class")

    # make it autograder tests
    _select_tests(browser)

    # click the id field
    element = browser.find_element_by_css_selector(".nbgrader-points-input")
    element.click()

    # get the active element
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-points-input" == element.get_attribute("class")

    # press tab and check that the active element is correct
    element.send_keys(Keys.TAB)
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-id-input" == element.get_attribute("class")


@pytest.mark.js
def test_total_points(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # make it autograder tests and set the points to two
    _select_tests(browser)
    _set_points(browser)
    _set_id(browser)
    assert _get_total_points(browser) == 2

    # make it a solution make sure the total points is zero
    _select_solution(browser)
    assert _get_total_points(browser) == 0

    # make it autograder tests
    _select_tests(browser)
    assert _get_total_points(browser) == 2

    # make it manually graded
    _select_manual(browser)
    assert _get_total_points(browser) == 2

    # create a new cell
    element = browser.find_element_by_tag_name("body")
    element.send_keys(Keys.ESCAPE)
    element.send_keys("b")

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            browser.find_elements_by_css_selector(".celltoolbar select")[1]
        except IndexError:
            return False
        return True
    WebDriverWait(browser, 30).until(find_toolbar)

    # make it a test cell
    _select_tests(browser, index=1)
    _set_points(browser, points=1, index=1)
    _set_id(browser, cell_id="bar", index=1)
    assert _get_total_points(browser) == 3

    # delete the new cell
    element = browser.find_elements_by_css_selector(".cell")[0]
    element.click()
    element.send_keys(Keys.ESCAPE)
    element.send_keys("d")
    element.send_keys("d")
    assert _get_total_points(browser) == 1

    # delete the first cell
    element = browser.find_elements_by_css_selector(".cell")[0]
    element.send_keys("d")
    element.send_keys("d")
    assert _get_total_points(browser) == 0
