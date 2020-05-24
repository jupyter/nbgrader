import pytest
import io
import os
import shutil
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from nbformat import write as write_nb
from nbformat.v4 import new_notebook
from textwrap import dedent

from .. import run_nbgrader
from .conftest import notwindows, _make_nbserver, _make_browser, _close_nbserver, _close_browser
from ...utils import rmtree

@pytest.fixture(scope='module')
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir,
             exchange, cache):
    server = _make_nbserver('', port, tempdir, jupyter_config_dir,
                            jupyter_data_dir, exchange, cache)

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


@pytest.fixture(scope="module")
def class_files(coursedir):
    # copy files from the user guide
    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source")
    shutil.copytree(os.path.join(os.path.dirname(__file__), source_path), os.path.join(coursedir, "source"))

    # rename to old names -- we do this rather than changing all the tests
    # because I want the tests to operate on files with spaces in the names
    os.rename(os.path.join(coursedir, "source", "ps1"), os.path.join(coursedir, "source", "Problem Set 1"))
    os.rename(os.path.join(coursedir, "source", "Problem Set 1", "problem1.ipynb"), os.path.join(coursedir, "source", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(os.path.join(coursedir, "source", "Problem Set 1", "problem2.ipynb"), os.path.join(coursedir, "source", "Problem Set 1", "Problem 2.ipynb"))

    # create a fake ps1
    os.mkdir(os.path.join(coursedir, "source", "ps.01"))
    with io.open(os.path.join(coursedir, "source", "ps.01", "problem 1.ipynb"), mode="w", encoding="utf-8") as fh:
        write_nb(new_notebook(), fh, 4)

    with open("nbgrader_config.py", "a") as fh:
        fh.write(dedent(
            """
            c.CourseDirectory.root = '{}'
            """.format(coursedir)
        ))

    return coursedir

def _wait(browser):
    return WebDriverWait(browser, 10)

def _find_element(browser: WebDriver, by, arg):
    _wait(browser).until(lambda x: browser.find_element(by, arg))
    element = browser.find_element(by, arg)
    _wait(browser).until(EC.visibility_of(element)) 

    return element


def _click_when_available(browser: WebDriver, by, arg):
    _wait(browser).until(lambda x: browser.find_element(by, arg))
    element = browser.find_element(by, arg)
    _wait(browser).until(EC.visibility_of(element))
    _click_element(browser, element)
    return element

def _click_element(browser: WebDriver, element):
    ActionChains(browser).click(element).perform()

def _get_element(browser: WebDriver, css_selector):
    try:
        return browser.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        return None

def _load_assignments_list(browser: WebDriver, port, retries=5):
    # go to the correct page
    browser.get("http://localhost:{}/lab".format(port))

    def page_loaded(browser):
        logo_id = 'jp-MainLogo'
        return len(browser.find_elements_by_id(logo_id)) > 0

    # wait for the page to load
    try:
        _wait(browser).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print("Retrying page load...")
            # page timeout, but sometimes this happens, so try refreshing?
            _load_assignments_list(browser, port, retries=retries - 1)
        else:
            print("Failed to load the page too many times")
            raise

    side_bar_selector = '[data-id="command-palette"]'
    al_selector = '[data-command="al:open"]'
    time.sleep(1)
    _click_when_available(browser, By.CSS_SELECTOR, side_bar_selector)
    _click_when_available(browser, By.CSS_SELECTOR, al_selector)

    # make sure released, downloaded, and submitted assignments are visible
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#released_assignments_list")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#fetched_assignments_list")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#submitted_assignments_list")))

def _wait_until_loaded(browser):
    _wait(browser).until(lambda browser: browser.find_element_by_id("course_list_default").text != "Loading, please wait...")
    _wait(browser).until(EC.element_to_be_clickable((By.ID, "course_list_dropdown")))
    

def _wait_for_list(browser, name, num_rows):
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#{}_assignments_list_loading".format(name))))
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#{}_assignments_list_placeholder".format(name))))
    _wait(browser).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#{}_assignments_list_error".format(name))))
    _wait(browser).until(lambda browser: len(browser.find_elements_by_css_selector("#{}_assignments_list > .list_item".format(name))) == num_rows)
    rows = browser.find_elements_by_css_selector("#{}_assignments_list > .list_item".format(name))
    assert len(rows) == num_rows
    return rows

def _change_course(browser, course):
    # wait until the dropdown is enabled
    _wait_until_loaded(browser)

    # click the dropdown to show the menu
    dropdown = browser.find_element_by_css_selector("#course_list_dropdown")
    dropdown.click()

    # parse the list of courses and click the one that's been requested
    courses = browser.find_elements_by_css_selector("#course_list > li")
    text = [x.text for x in courses]
    index = text.index(course)
    courses[index].click()

    # wait for the dropdown to be disabled, then enabled again
    _wait_until_loaded(browser)

    # verify the dropdown shows the correct course
    default = browser.find_element_by_css_selector("#course_list_default")
    assert default.text == course

def _expand(browser, list_id, assignment):
    browser.find_element_by_id("fetched_assignments_list").find_element_by_link_text(assignment).click()
    rows = browser.find_elements_by_css_selector("{} .list_item".format(list_id))
    for i in range(1, len(rows)):
        _wait(browser).until(lambda browser: browser.find_elements_by_css_selector("{} .list_item".format(list_id))[i].is_displayed())
    return rows

def _unexpand(browser, list_id, assignment):
    browser.find_element_by_link_text(assignment).click()
    rows = browser.find_elements_by_css_selector("{} .list_item".format(list_id))
    for i in range(1, len(rows)):
        _wait(browser).until(lambda browser: not browser.find_elements_by_css_selector("{} .list_item".format(list_id))[i].is_displayed())

def _sort_rows(x):
    try:
        item_name = x.find_element_by_class_name("item_name").text
    except NoSuchElementException:
        item_name = ""
    return item_name

def _dismiss_modal(browser):
    ok_button = 'jp-Dialog-button'
    _click_when_available(browser, By.CLASS_NAME, ok_button)

def _wait_for_modal(browser):
    
    class_selector = 'jp-Dialog-content'
    _wait(browser).until(EC.presence_of_all_elements_located((By.CLASS_NAME, class_selector)))

@pytest.mark.nbextensions
@notwindows
def test_show_assignments_list(browser, port, class_files, tempdir):
    _load_assignments_list(browser, port)
    _wait_until_loaded(browser)

    # make sure all the placeholders are initially showing
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#released_assignments_list_placeholder")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#fetched_assignments_list_placeholder")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#submitted_assignments_list_placeholder")))

    # release an assignment
    run_nbgrader(["generate_assignment", "Problem Set 1", "--force"])
    run_nbgrader(["release_assignment", "Problem Set 1", "--course", "abc101", "--force"])

    browser.refresh()
    time.sleep(5)
    # click the refresh button
    browser.find_element_by_css_selector("#refresh_assignments_list").click()
    _wait_until_loaded(browser)

    # wait for the released assignments to update
    rows = _wait_for_list(browser, "released", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "Problem Set 1"
    assert rows[0].find_element_by_class_name("item_course").text == "abc101"


@notwindows
def test_multiple_released_assignments(browser, port, class_files, tempdir):
    # release another assignment
    run_nbgrader(["generate_assignment", "ps.01", "--force"])
    run_nbgrader(["release_assignment", "ps.01", "--course", "xyz 200", "--force"])
    time.sleep(5)
    # click the refresh button
    browser.find_element_by_css_selector("#refresh_assignments_list").click()
    _wait_until_loaded(browser)

    # choose the course "xyz 200"
    _change_course(browser, "xyz 200")
    
    rows = _wait_for_list(browser, "released", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"


@pytest.mark.nbextensions
@notwindows
def test_fetch_assignment(browser, port, class_files, tempdir):
    # choose the course "xyz 200"
    _change_course(browser, "xyz 200")
    # click the "fetch" button
    rows = _wait_for_list(browser, "released", 1)
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the downloaded assignments list to update
    rows = _wait_for_list(browser, "fetched", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"
    assert os.path.exists(os.path.join(tempdir, "ps.01"))

    # expand the assignment to show the notebooks
    rows = _expand(browser, "#nbgrader-xyz_200-ps01", "ps.01")
    rows.sort(key=_sort_rows)
    assert len(rows) == 2
    assert rows[1].find_element_by_class_name("item_name").text == "problem 1"

    # unexpand the assignment
    _unexpand(browser, "#nbgrader-xyz_200-ps01", "ps.01")


@pytest.mark.nbextensions
@notwindows
def test_submit_assignment(browser, port, class_files, tempdir):
    # submit it
    rows = _wait_for_list(browser, "fetched", 1)
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the submitted assignments list to update
    rows = _wait_for_list(browser, "submitted", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"
    rows = browser.find_elements_by_css_selector("#nbgrader-xyz_200-ps01-submissions > .list_item")
    rows = rows[1:]  # first row is empty
    assert len(rows) == 1

    # submit it again
    rows = browser.find_elements_by_css_selector("#fetched_assignments_list > .list_item")
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the submitted assignments list to update
    rows = _wait_for_list(browser, "submitted", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"
    rows = browser.find_elements_by_css_selector("#nbgrader-xyz_200-ps01-submissions > .list_item")
    rows = rows[1:]  # first row is empty
    assert len(rows) == 2
    timestamp1 = rows[0].find_element_by_css_selector(".item_name").text
    timestamp2 = rows[1].find_element_by_css_selector(".item_name").text
    assert timestamp1 != timestamp2

@pytest.mark.nbextensions
@notwindows
def test_submit_assignment_missing_notebooks(browser, port, class_files, tempdir):
    # rename an assignment notebook
    assert os.path.exists(os.path.join(tempdir, "ps.01"))
    if os.path.isfile(os.path.join(tempdir, "ps.01", "problem 1.ipynb")):
        os.rename(
            os.path.join(tempdir, "ps.01", "problem 1.ipynb"),
            os.path.join(tempdir, "ps.01", "my problem 1.ipynb")
        )

    # submit it again
    rows = browser.find_elements_by_css_selector("#fetched_assignments_list > .list_item")
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the submitted assignments list to update
    rows = _wait_for_list(browser, "submitted", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"
    
    rows = browser.find_elements_by_css_selector("#nbgrader-xyz_200-ps01-submissions > .list_item")
    rows = rows[1:]  # first row is empty
    assert len(rows) == 3
    timestamp1 = rows[0].find_element_by_css_selector(".item_name").text
    timestamp2 = rows[1].find_element_by_css_selector(".item_name").text
    timestamp3 = rows[2].find_element_by_css_selector(".item_name").text
    assert timestamp1 != timestamp2
    assert timestamp2 != timestamp3
    
    # set strict flag
    with open('nbgrader_config.py', 'a') as config:
        config.write('c.ExchangeSubmit.strict = True')

    # submit it again
    rows = browser.find_elements_by_css_selector("#fetched_assignments_list > .list_item")
    rows[0].find_element_by_css_selector(".item_status button").click()

    
    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that the submission failed
    assert browser.find_element_by_class_name("jp-Dialog-header").text == "Invalid Submission"
    
    # close the modal dialog
    _dismiss_modal(browser)

    
    # check submitted assignments list remains unchanged
    rows = _wait_for_list(browser, "submitted", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "ps.01"
    assert rows[0].find_element_by_class_name("item_course").text == "xyz 200"
    rows = browser.find_elements_by_css_selector("#nbgrader-xyz_200-ps01-submissions > .list_item")
    rows = rows[1:]  # first row is empty
    assert len(rows) == 3

    # clean up for following tests: rename notebook back to original name
    assert os.path.exists(os.path.join(tempdir, "ps.01"))
    if os.path.isfile(os.path.join(tempdir, "ps.01", "my problem 1.ipynb")):
        os.rename(
            os.path.join(tempdir, "ps.01", "my problem 1.ipynb"),
            os.path.join(tempdir, "ps.01", "problem 1.ipynb")
        )
    
@pytest.mark.nbextensions
@notwindows
def test_fetch_second_assignment(browser, port, class_files, tempdir):
    # click the "fetch" button
    _change_course(browser, "abc101")
    rows = _wait_for_list(browser, "released", 1)
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the downloaded assignments list to update
    rows = _wait_for_list(browser, "fetched", 1)
    rows.sort(key=_sort_rows)
    assert rows[0].find_element_by_class_name("item_name").text == "Problem Set 1"
    assert rows[0].find_element_by_class_name("item_course").text == "abc101"
    assert os.path.exists(os.path.join(tempdir, "Problem Set 1"))

    # expand the assignment to show the notebooks
    rows = _expand(browser, "#nbgrader-abc101-Problem_Set_1", "Problem Set 1")
    rows.sort(key=_sort_rows)
    assert len(rows) == 3
    assert rows[1].find_element_by_class_name("item_name").text == "Problem 1"
    assert rows[2].find_element_by_class_name("item_name").text == "Problem 2"

    # unexpand the assignment
    _unexpand(browser, "abc101-Problem_Set_1", "Problem Set 1")


@pytest.mark.nbextensions
@notwindows
def test_submit_other_assignment(browser, port, class_files, tempdir):
    # submit it
    rows = _wait_for_list(browser, "fetched", 1)
    rows[0].find_element_by_css_selector(".item_status button").click()

    # wait for the submitted assignments list to update
    rows = _wait_for_list(browser, "submitted", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "Problem Set 1"
    assert rows[0].find_element_by_class_name("item_course").text == "abc101"
    rows = browser.find_elements_by_css_selector("#nbgrader-abc101-Problem_Set_1-submissions > .list_item")
    rows = rows[1:]  # first row is empty
    assert len(rows) == 1

@pytest.mark.nbextensions
@notwindows
def test_validate_ok(browser, port, class_files, tempdir):
    # choose the course "xyz 200"
    _change_course(browser, "xyz 200")

    # expand the assignment to show the notebooks
    _wait_for_list(browser, "fetched", 1)
    rows = _expand(browser, "#nbgrader-xyz_200-ps01", "ps.01")
    rows.sort(key=_sort_rows)
    assert len(rows) == 2
    assert rows[1].find_element_by_class_name("item_name").text == "problem 1"

    # click the "validate" button
    rows[1].find_element_by_css_selector(".item_status button").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    assert browser.find_element_by_class_name("jp-Dialog-header").text == "Validation Results"
    #browser.find_element_by_css_selector(".modal-dialog .validation-success")

    # close the modal dialog
    _dismiss_modal(browser)

@pytest.mark.nbextensions
@notwindows
def test_validate_failure(browser, port, class_files, tempdir):
    #chagne couse
    _change_course(browser, "abc101")

    # expand the assignment to show the notebooks
    _wait_for_list(browser, "fetched", 1)
    rows = _expand(browser, "#nbgrader-abc101-Problem_Set_1", "Problem Set 1")
    rows.sort(key=_sort_rows)
    assert len(rows) == 3
    assert rows[1].find_element_by_class_name("item_name").text == "Problem 1"
    assert rows[2].find_element_by_class_name("item_name").text == "Problem 2"

    # click the "validate" button
    rows[2].find_element_by_css_selector(".item_status button").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    assert browser.find_element_by_class_name("jp-Dialog-header").text == "Validation Results"

    # close the modal dialog
    _dismiss_modal(browser)

@pytest.mark.nbextensions
@notwindows
def test_missing_exchange(exchange, browser, port, class_files, tempdir):
    # remove the exchange directory and fetched assignments
    rmtree(exchange)
    rmtree(os.path.join(tempdir, "Problem Set 1"))

    # click the refresh button
    browser.find_element_by_css_selector("#refresh_assignments_list").click()
    _wait_until_loaded(browser)

    # make sure all the errors are showing
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#released_assignments_list_error")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#fetched_assignments_list_error")))
    _wait(browser).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#submitted_assignments_list_error")))

    # verify that the dropdown list shows an error too
    default = browser.find_element_by_css_selector("#course_list_default")
    assert default.text == "Error fetching courses!"

    # recreate the exchange and make sure refreshing works as expected
    os.makedirs(exchange)

    # release an assignment
    run_nbgrader(["generate_assignment", "Problem Set 1", "--force"])
    run_nbgrader(["release_assignment", "Problem Set 1", "--course", "abc101", "--force"])

    browser.refresh()
    time.sleep(1)
    # click the refresh button
    browser.find_element_by_css_selector("#refresh_assignments_list").click()
    _wait_until_loaded(browser)

    # wait for the released assignments to update
    rows = _wait_for_list(browser, "released", 1)
    assert rows[0].find_element_by_class_name("item_name").text == "Problem Set 1"
    assert rows[0].find_element_by_class_name("item_course").text == "abc101"
