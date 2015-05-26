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
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctb_select')))

def _activate_toolbar(browser, name="Create Assignment"):
    # activate the Create Assignment toolbar
    element = browser.find_element_by_css_selector("#ctb_select")
    select = Select(element)
    select.select_by_visible_text(name)


def _click_solution(browser):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell(0);
        var elems = cell.element.find(".button_container");
        $(elems[3]).find("input").click();
        """
    )


def _click_grade(browser, index=0):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell({});
        var elems = cell.element.find(".button_container");
        $(elems[2]).find("input").click();
        """.format(index)
    )


def _set_points(browser, points=2, index=0):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell({});
        var elem = cell.element.find(".nbgrader-points-input");
        elem.val("{}");
        elem.trigger("change");
        """.format(index, points)
    )


def _set_grade_id(browser):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell(0);
        var elem = cell.element.find(".nbgrader-id-input");
        elem.val("foo");
        elem.trigger("change");
        """
    )


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


def test_create_assignment(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the toolbar appeared
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar input")))
    assert element[0].get_attribute("type") == "checkbox"

    # does the nbgrader metadata exist?
    assert {} == _get_metadata(browser)

    # click the "solution?" checkbox
    _click_solution(browser)
    assert _get_metadata(browser)['solution']

    # unclick the "solution?" checkbox
    _click_solution(browser)
    assert not _get_metadata(browser)['solution']

    # click the "grade?" checkbox
    _click_grade(browser)
    assert _get_metadata(browser)['grade']

    # wait for the points and id fields to appear
    WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-points")))
    WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    _set_grade_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # unclick the "grade?" checkbox
    _click_grade(browser)
    assert not _get_metadata(browser)['grade']


def test_grade_cell_css(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # click the "grade?" checkbox
    _click_grade(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 1

    # unclick the "grade?" checkbox
    _click_grade(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 0

    # click the "grade?" checkbox
    _click_grade(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 1

    # deactivate the toolbar
    _activate_toolbar(browser, "None")
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 0

    # activate the toolbar
    _activate_toolbar(browser)
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 1

    # deactivate the toolbar
    _activate_toolbar(browser, "Edit Metadata")
    elements = browser.find_elements_by_css_selector(".nbgrader-grade-cell")
    assert len(elements) == 0


def test_tabbing(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # click the "grade?" checkbox
    _click_grade(browser)

    # click the id field
    element = browser.find_element_by_css_selector(".nbgrader-id-input")
    element.click()

    # get the active element
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-id-input" == element.get_attribute("class")

    # press tab and check that the active element is correct
    element.send_keys(Keys.TAB)
    element = browser.execute_script("return document.activeElement")
    assert "nbgrader-points-input" == element.get_attribute("class")


def test_total_points(browser):
    _load_notebook(browser)
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # click the "grade?" checkbox and set the points to two
    _click_grade(browser)
    _set_points(browser)
    assert _get_total_points(browser) == 2

    # unclick the "grade?" checkbox and make sure the total points is zero
    _click_grade(browser)
    assert _get_total_points(browser) == 0

    # click the "grade?" checkbox
    _click_grade(browser)
    assert _get_total_points(browser) == 2

    # create a new cell
    element = browser.find_element_by_tag_name("body")
    element.send_keys(Keys.ESCAPE)
    element.send_keys("b")

    # click the "grade?" checkbox
    _click_grade(browser, index=1)
    _set_points(browser, points=1, index=1)
    assert _get_total_points(browser) == 3

    # delete the new cell
    element.send_keys("dd")
    assert _get_total_points(browser) == 2

    # delete the first cell
    element.send_keys("dd")
    assert _get_total_points(browser) == 0
