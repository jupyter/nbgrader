import json
import os
import time

from nbformat import current_nbformat
import pytest
from selenium.common.exceptions import (NoSuchElementException,
                                        NoAlertPresentException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait

from .conftest import (_close_browser, _close_nbserver, _make_browser,
                       _make_nbserver)
from ...nbgraderformat import read


@pytest.fixture(scope='module')
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir,
             exchange, cache):
    server = _make_nbserver('', port, tempdir, jupyter_config_dir,
                            jupyter_data_dir, exchange, cache)

    def fin():
        _close_nbserver(server)
    request.addfinalizer(fin)

    return server


@pytest.fixture(scope='module')
def browser(request, tempdir, nbserver):
    browser = _make_browser(tempdir)

    def fin():
        _close_browser(browser)
    request.addfinalizer(fin)

    return browser


def _activate_toolbar(browser: WebDriver):
    tab_selector = '[data-id="nbgrader-create_assignemnt"]'
    tab_element = browser.find_element_by_css_selector(tab_selector)
    _click_element(browser, tab_element)


def _click_element(browser: WebDriver, element):
    ActionChains(browser).click(element).perform()


def _click_when_available(browser: WebDriver, by, arg):
    _wait(browser).until(lambda x: browser.find_element(by, arg))
    element = browser.find_element(by, arg)
    _wait(browser).until(expected_conditions.visibility_of(element))
    _click_element(browser, element)
    return element


def _create_new_cell(browser: WebDriver):
    notebook_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) ' \
                        '.jp-NotebookPanel-notebook'
    notebook_element = browser.find_element_by_css_selector(notebook_selector)
    notebook_element.send_keys(Keys.ESCAPE)
    notebook_element.send_keys("b")


def _delete_cell(browser: WebDriver, index=0):
    cell_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) .jp-InputPrompt'
    cell_elements = browser.find_elements_by_css_selector(cell_selector)
    element = cell_elements[index]
    element.click()
    ActionChains(browser).send_keys('dd').perform()


def _dismiss_modal(browser: WebDriver):
    selector = '.jp-Dialog button.jp-mod-accept'
    accept_button = browser.find_element_by_css_selector(selector)
    accept_button.click()
    _wait(browser).until(expected_conditions.staleness_of(accept_button))


def _get_element(browser: WebDriver, css_selector):
    try:
        return browser.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        return None


def _get_kernel(browser: WebDriver):
    kernel_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) .jp-KernelName'
    _wait(browser).until(expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, kernel_selector)))
    kernel_element = _get_element(browser, kernel_selector)
    return kernel_element.text


def _get_highlighted_cells(browser: WebDriver):
    selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
               '.nbgrader-mod-highlight'
    return browser.find_elements_by_css_selector(selector)


def _get_metadata(browser: WebDriver):
    advanced_tools_selector = '#jp-left-stack .jp-Collapse-header'
    cell_metadata_selector = '.jp-MetadataEditorTool .CodeMirror-code'
    inspector_panel_selector = '#jp-left-stack .jp-PropertyInspector'
    inspector_tab_selector = '.jp-SideBar [data-id="jp-property-inspector"]'

    inspector_panel_element = _get_element(browser, inspector_panel_selector)
    if not inspector_panel_element.is_displayed():
        # Open the property inspector.
        _click_when_available(browser, By.CSS_SELECTOR, inspector_tab_selector)

    editor_element = _get_element(browser, cell_metadata_selector)
    if not editor_element.is_displayed():
        # Expand "Advanced Tools".
        _click_when_available(browser, By.CSS_SELECTOR,
                              advanced_tools_selector)

    metadata = None
    while not metadata:
        time.sleep(0.1)
        metadata = editor_element.text
    # Use proper spaces.
    metadata = metadata.replace(u'\xa0', u' ')
    metadata = json.loads(metadata)
    key = 'nbgrader'
    if key in metadata:
        return metadata[key]
    return None


def _get_toolbar_cells(browser: WebDriver):
    selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
               '.nbgrader-CellWidget'
    elements = browser.find_elements_by_css_selector(selector)
    return elements


def _get_total_points(browser: WebDriver) -> int:
    selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
               '.nbgrader-NotebookPoints input'
    element = browser.find_element_by_css_selector(selector)
    points = element.get_attribute('value')
    return int(points)


def _load_notebook(browser: WebDriver, port, retries=4, name='blank',
                   expect_schema_modal=False):
    # go to the correct page
    url = 'http://localhost:{}/lab'.format(port)
    for i in range(4):
        try:
            browser.get(url)
            break
        except WebDriverException:
            time.sleep(5)

    alert = ''
    for _ in range(5):
        if alert is None:
            break

        try:
            alert = browser.switch_to.alert
        except NoAlertPresentException:
            alert = None
        else:
            print('Warning: dismissing unexpected alert ({})'
                  .format(alert.text))
            alert.accept()

    def page_loaded(browser: WebDriver):
        logo_id = 'jp-MainLogo'
        return len(browser.find_elements_by_id(logo_id)) > 0

    # wait for the page to load
    try:
        _wait(browser).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print('Retrying page load...')
            # page timeout, but sometimes this happens, so try refreshing?
            _load_notebook(browser, port, retries=retries - 1, name=name)
        else:
            print('Failed to load the page too many times')
            raise

    accept_selector = 'jp-mod-accept'
    active_tab_label_selector = '#jp-main-dock-panel ' \
                                '.lm-TabBar-tab.lm-mod-current ' \
                                '.lm-TabBar-tabLabel'
    delete_cell_selector = '.lm-Menu-item[data-command="notebook:delete-cell"]'
    edit_selector = '.lm-MenuBar-item:nth-child(2)'
    file_class = 'lm-MenuBar-item'
    notebook_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) ' \
                        + '.jp-NotebookPanel-notebook'
    open_from_path_selector = '.lm-Menu-item' \
                              + '[data-command="filebrowser:open-path"]'
    path_input_selector = '.jp-Input-Dialog input'
    select_all_selector = '.lm-Menu-item[data-command="notebook:select-all"]'

    time.sleep(1)
    file_menu = _click_when_available(browser, By.CLASS_NAME, file_class)
    height = file_menu.get_property('offsetHeight')
    ActionChains(browser).move_by_offset(0, height / 2).perform()
    _click_when_available(browser, By.CSS_SELECTOR, open_from_path_selector)
    path_input_element = _click_when_available(browser, By.CSS_SELECTOR,
                                               path_input_selector)
    path_input_element.send_keys(name + '.ipynb')
    open_element = _click_when_available(browser, By.CLASS_NAME,
                                         accept_selector)
    _wait(browser).until(expected_conditions.staleness_of(open_element))
    _wait(browser).until(expected_conditions.text_to_be_present_in_element(
            (By.CSS_SELECTOR, active_tab_label_selector),
            '{}.ipynb'.format(name)))
    if expect_schema_modal:
        _wait_for_modal(browser, title='Outdated schema version')
        _dismiss_modal(browser)
    if 'Kernel' == _get_kernel(browser):
        select_element = _click_when_available(browser, By.CLASS_NAME,
                                               accept_selector)
        _wait(browser).until(expected_conditions.staleness_of(
            select_element))

    if name == 'blank':
        # Delete all cells.
        edit_element = _click_when_available(browser, By.CSS_SELECTOR,
                                             edit_selector)
        _click_when_available(browser, By.CSS_SELECTOR, select_all_selector)
        _click_element(browser, edit_element)
        _click_when_available(browser, By.CSS_SELECTOR, delete_cell_selector)
        return


def _save(browser: WebDriver):
    file_class = 'lm-MenuBar-item'
    save_selector = '.lm-Menu-item[data-command="docmanager:save"]'
    if _get_element(browser, save_selector) is None:
        _click_when_available(browser, By.CLASS_NAME, file_class)
    _click_when_available(browser, By.CSS_SELECTOR, save_selector)

    def is_saved(browser: WebDriver):
        closable_tab_selector = '.jp-mod-current.lm-mod-closable'
        return _get_element(browser, closable_tab_selector) is not None

    return is_saved


def _save_and_validate(browser: WebDriver):
    _wait(browser).until(_save(browser))
    time.sleep(2)
    read('blank.ipynb', current_nbformat)


def _save_screenshot(browser: WebDriver):
    browser.save_screenshot(os.path.join(os.path.dirname(__file__),
                            'selenium.screenshot.png'))


def _select(browser: WebDriver, text, index=0):
    type_selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) select'

    def is_clickable(browser: WebDriver):
        elements = browser.find_elements_by_css_selector(type_selector)
        if len(elements) <= index:
            return False
        element = elements[index]
        return element.is_displayed and element.is_enabled

    def is_option(browser: WebDriver):
        element = browser.find_elements_by_css_selector(type_selector)[index]
        select = Select(element)
        options = [x.get_attribute('value') for x in select.options]
        return text in options

    _wait(browser).until(is_clickable)
    _wait(browser).until(is_option)
    element = browser.find_elements_by_css_selector(type_selector)[index]
    select = Select(element)
    select.select_by_value(text)

    def selected(browser: WebDriver):
        element = browser.find_elements_by_css_selector(type_selector)[index]
        return element.get_attribute('value') == text

    _wait(browser).until(selected)


def _select_locked(browser, index=0):
    _select(browser, 'readonly', index=index)


def _select_manual(browser: WebDriver, index=0):
    _select(browser, 'manual', index=index)


def _select_none(browser: WebDriver, index=0):
    _select(browser, '', index=index)


def _select_solution(browser, index=0):
    _select(browser, 'solution', index=index)


def _select_task(browser: WebDriver, index=0):
    _select(browser, 'task', index=index)


def _select_tests(browser, index=0):
    _select(browser, 'tests', index=index)


def _set_id(browser: WebDriver, cell_id='foo', index=0):
    id_selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
                  '.nbgrader-CellId input'
    element = browser.find_elements_by_css_selector(id_selector)[index]
    element.clear()
    element.send_keys(cell_id)
    element.send_keys(Keys.ENTER)


def _set_points(browser: WebDriver, points=2, index=0):
    points_selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
                      '.nbgrader-CellPoints input'
    element = browser.find_elements_by_css_selector(points_selector)[index]
    element.clear()
    element.send_keys(str(points))
    element.send_keys(Keys.ENTER)


def _set_to_markdown(browser: WebDriver):
    notebook_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) ' \
                        '.jp-NotebookPanel-notebook'
    notebook_element = browser.find_element_by_css_selector(notebook_selector)
    notebook_element.send_keys(Keys.ESCAPE)
    notebook_element.send_keys("m")


def _wait(browser: WebDriver):
    return WebDriverWait(browser, 30)

def _wait_for_modal(browser: WebDriver, title=None):
    class_name = 'jp-Dialog'
    condition = expected_conditions.presence_of_element_located((
            By.CLASS_NAME, class_name))
    element = _wait(browser).until(condition)
    if title is not None:
        header_class = 'jp-Dialog-header'
        header_text = element.find_element_by_id(header_class).text
        assert title == header_text


@pytest.mark.labextensions
def test_manual_cell(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it manually graded
    _select_manual(browser)
    assert _get_metadata(browser)['solution']
    assert _get_metadata(browser)['grade']
    assert not _get_metadata(browser)['locked']

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith('cell-')
    _set_id(browser)
    assert 'foo' == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_task_cell(browser: WebDriver, port):
    _load_notebook(browser, port, name='task')
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it manually graded
    _select_task(browser)
    assert _get_metadata(browser)['task']
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert _get_metadata(browser)['locked']

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_solution_cell(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it a solution cell
    _select_solution(browser)
    assert _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert not _get_metadata(browser)['locked']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_tests_cell(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it autograder tests
    _select_tests(browser)
    assert not _get_metadata(browser)['solution']
    assert _get_metadata(browser)['grade']
    assert _get_metadata(browser)['locked']

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_tests_to_solution_cell(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it autograder tests
    _select_tests(browser)
    assert not _get_metadata(browser)['solution']
    assert _get_metadata(browser)['grade']
    assert _get_metadata(browser)['locked']

    # set the points
    _set_points(browser)
    assert 2 == _get_metadata(browser)['points']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it a solution cell and make sure the points are gone
    _select_solution(browser)
    assert _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert not _get_metadata(browser)['locked']
    assert 'points' not in _get_metadata(browser)
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_locked_cell(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # does the nbgrader metadata exist?
    assert _get_metadata(browser) is None

    # make it locked
    _select_locked(browser)
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert _get_metadata(browser)['locked']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert "foo" == _get_metadata(browser)['grade_id']

    # make sure the metadata is valid
    _save_and_validate(browser)

    # make it nothing
    _select_none(browser)
    assert not _get_metadata(browser)
    _save_and_validate(browser)


@pytest.mark.labextensions
def test_grade_cell_css(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # make it manually graded
    _select_manual(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 0

    # make it a solution
    _select_solution(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 0

    # make it autograder tests
    _select_tests(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 1

    # make it nothing
    _select_none(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 0

    # make it autograder tests
    _select_tests(browser)
    elements = _get_highlighted_cells(browser)
    assert len(elements) == 1


@pytest.mark.labextensions
def test_tabbing(browser: WebDriver, port):
    id_selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
                  '.nbgrader-CellId input'
    points_selector = '.nbgrader-NotebookPanelWidget:not(.lm-mod-hidden) ' \
                      '.nbgrader-CellPoints input'

    _load_notebook(browser, port)
    _activate_toolbar(browser)

    def active_element_is(element):
        def waitfor(browser):
            active = browser.switch_to.active_element
            return element == active
        return waitfor

    id_element = browser.find_element_by_css_selector(id_selector)
    points_element = browser.find_element_by_css_selector(points_selector)

    # make it manually graded
    _select_manual(browser)

    # click the id field
    element = id_element
    element.click()
    element.send_keys(Keys.RETURN)
    _wait(browser).until(active_element_is(id_element))

    # press tab and check that the active element is correct
    element.send_keys(Keys.TAB)
    _wait(browser).until(active_element_is(points_element))

    # make it autograder tests
    _select_tests(browser)

    # click the id field
    element = id_element
    element.click()
    element.send_keys(Keys.RETURN)
    _wait(browser).until(active_element_is(id_element))

    # press tab and check that the active element is correct
    element.send_keys(Keys.TAB)
    _wait(browser).until(active_element_is(points_element))


@pytest.mark.labextensions
def test_total_points(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # make it autograder tests and set the points to two
    _select_tests(browser)
    _set_points(browser)
    _set_id(browser)
    assert _get_total_points(browser) == 2

    # make it manually graded
    _select_manual(browser)
    assert _get_total_points(browser) == 2

    # make it a solution make sure the total points is zero
    _select_solution(browser)
    assert _get_total_points(browser) == 0

    # make it autograder tests
    _select_tests(browser)
    assert _get_total_points(browser) == 0
    _set_points(browser)
    assert _get_total_points(browser) == 2

    # create a new cell
    _create_new_cell(browser)

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            _get_toolbar_cells(browser)[1]
        except IndexError:
            return False
        return True
    _wait(browser).until(find_toolbar)

    # make it a test cell
    _select_tests(browser, index=1)
    _set_points(browser, points=1, index=1)
    _set_id(browser, cell_id="bar", index=1)
    assert _get_total_points(browser) == 3

    # delete the new cell
    _delete_cell(browser, 1)
    assert _get_total_points(browser) == 2

    # delete the first cell
    _delete_cell(browser, 0)
    assert _get_total_points(browser) == 0


@pytest.mark.labextensions
def test_total_points(browser: WebDriver, port):
    _load_notebook(browser, port, 'task')
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # make it autograder tests and set the points to two
    _select_task(browser)
    _set_points(browser)
    _set_id(browser)
    assert _get_total_points(browser) == 2

    # make it manually graded
    _select_manual(browser)
    assert _get_total_points(browser) == 2

    # make it a solution make sure the total points is zero
    _select_solution(browser)
    assert _get_total_points(browser) == 0

    # make it task
    _select_task(browser)
    assert _get_total_points(browser) == 0
    _set_points(browser)
    assert _get_total_points(browser) == 2

    # create a new cell
    _create_new_cell(browser)

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            _get_toolbar_cells(browser)[1]
        except IndexError:
            return False
        return True
    _wait(browser).until(find_toolbar)

    # make it a test cell
    _select_tests(browser, index=1)
    _set_points(browser, points=1, index=1)
    _set_id(browser, cell_id="bar", index=1)
    assert _get_total_points(browser) == 3

    # delete the new cell
    _delete_cell(browser, 1)
    assert _get_total_points(browser) == 2

    # delete the first cell
    _delete_cell(browser, 0)
    assert _get_total_points(browser) == 0


@pytest.mark.labextensions
def test_cell_ids(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # turn it into a cell with an id
    _select_solution(browser)
    # for some reason only one call doesn't trigger on_change event
    _select_solution(browser)
    _set_id(browser, cell_id="")

    # save and check for an error (blank id)
    _save(browser)
    _wait_for_modal(browser)
    _dismiss_modal(browser)

    # set the label
    _set_id(browser)

    # create a new cell
    _create_new_cell(browser)

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            _get_toolbar_cells(browser)[1]
        except IndexError:
            return False
        return True
    _wait(browser).until(find_toolbar)

    # make it a test cell and set the label
    _select_tests(browser, index=1)
    _set_id(browser, index=1)

    # save and check for an error (duplicate id)
    _save(browser)
    _wait_for_modal(browser)
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_task_cell_ids(browser: WebDriver, port):
    _load_notebook(browser, port, name='task')
    _activate_toolbar(browser)

    # turn it into a cell with an id
    _select_task(browser)
    _set_id(browser, cell_id="")

    # save and check for an error (blank id)
    _save(browser)
    _wait_for_modal(browser)
    _dismiss_modal(browser)

    # set the label
    _set_id(browser)

    # create a new cell
    _create_new_cell(browser)

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            _get_toolbar_cells(browser)[1]
        except IndexError:
            return False
        return True
    _wait(browser).until(find_toolbar)

    # make it a test cell and set the label
    _select_task(browser, index=1)
    _set_id(browser, index=1)

    # save and check for an error (duplicate id)
    _save(browser)
    _wait_for_modal(browser)
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_negative_points(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # make it autograder tests and set the points to two
    _select_tests(browser)
    _set_points(browser, points=2)
    _set_id(browser)
    assert _get_total_points(browser) == 2
    assert 2 == _get_metadata(browser)['points']

    # set the points to negative one
    _set_points(browser, points=-1)
    assert _get_total_points(browser) == 0
    assert 0 == _get_metadata(browser)['points']


@pytest.mark.labextensions
def test_task_negative_points(browser: WebDriver, port):
    _load_notebook(browser, port, 'task')
    _activate_toolbar(browser)

    # make sure the total points is zero
    assert _get_total_points(browser) == 0

    # make it autograder tests and set the points to two
    _select_task(browser)
    _set_points(browser, points=2)
    _set_id(browser)
    assert _get_total_points(browser) == 2
    assert 2 == _get_metadata(browser)['points']

    # set the points to negative one
    _set_points(browser, points=-1)
    assert _get_total_points(browser) == 0
    assert 0 == _get_metadata(browser)['points']


@pytest.mark.labextensions
def test_schema_version(browser: WebDriver, port):
    _load_notebook(browser, port, name="old-schema", expect_schema_modal=True)


@pytest.mark.labextensions
def test_invalid_nbgrader_cell_type(browser: WebDriver, port):
    _load_notebook(browser, port)
    _activate_toolbar(browser)

    # make it a solution cell
    _select_solution(browser)
    assert _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert not _get_metadata(browser)['locked']

    # set the id
    assert _get_metadata(browser)['grade_id'].startswith("cell-")
    _set_id(browser)
    assert _get_metadata(browser)['grade_id'] == "foo"

    # make sure the metadata is valid
    _save_and_validate(browser)

    # change the cell to a markdown cell
    _set_to_markdown(browser)

    # make sure the toolbar appeared
    def find_toolbar(browser):
        try:
            _get_toolbar_cells(browser)[0]
        except IndexError:
            return False
        return True
    _wait(browser).until(find_toolbar)

    # check that then nbgrader metadata is consistent
    assert not _get_metadata(browser)['solution']
    assert not _get_metadata(browser)['grade']
    assert not _get_metadata(browser)['locked']
    assert _get_metadata(browser)['grade_id'] == "foo"
