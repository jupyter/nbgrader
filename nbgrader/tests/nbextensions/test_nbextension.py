from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


def _activate_toolbar(browser, name="Create Assignment", try_again=True):
    def page_loaded(browser):
        return browser.execute_script(
            'return typeof IPython !== "undefined" && IPython.page !== undefined;')

    # wait for the page to load
    try:
        WebDriverWait(browser, 30).until(page_loaded)
    except TimeoutException:
        if try_again:
            # page timeout, but sometimes this happens, so try refreshing?
            browser.refresh()
            _activate_toolbar(browser, name=name, try_again=False)
        else:
            raise

    # wait for the celltoolbar menu to appear
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctb_select')))

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


def _click_grade(browser):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell(0);
        var elems = cell.element.find(".button_container");
        $(elems[2]).find("input").click();
        """
    )


def _set_points(browser):
    browser.execute_script(
        """
        var cell = IPython.notebook.get_cell(0);
        var elem = cell.element.find(".nbgrader-points-input");
        elem.val("2");
        elem.trigger("change");
        """
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


def test_create_assignment(browser):
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
