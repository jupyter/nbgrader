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


def _load_notebook(browser: WebDriver, port, retries=4, name='blank'):
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
    delete_cell_selector = '.lm-Menu-item[data-command="notebook:delete-cell"]'
    edit_selector = '.lm-MenuBar-item:nth-child(2)'
    file_class = 'lm-MenuBar-item'
    open_from_path_selector = '.lm-Menu-item' \
                              + '[data-command="filebrowser:open-path"]'
    path_input_selector = '.jp-Input-Dialog input'
    select_all_selector = '.lm-Menu-item[data-command="notebook:select-all"]'

    time.sleep(1)
    _click_when_available(browser, By.CLASS_NAME, file_class)
    _click_when_available(browser, By.CSS_SELECTOR, open_from_path_selector)
    path_input_element = _click_when_available(browser, By.CSS_SELECTOR,
                                               path_input_selector)
    path_input_element.send_keys(name + '.ipynb')
    open_element = _click_when_available(browser, By.CLASS_NAME,
                                         accept_selector)
    _wait(browser).until(expected_conditions.staleness_of(open_element))
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
    read('blank.ipynb', current_nbformat)


def _save_screenshot(browser: WebDriver):
    browser.save_screenshot(os.path.join(os.path.dirname(__file__),
                            'selenium.screenshot.png'))


def _select(browser: WebDriver, text, index=0):
    type_selector = '.nbgrader-CellType select'

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


def _select_manual(browser: WebDriver, index=0):
    _select(browser, 'manual', index=index)


def _select_none(browser: WebDriver, index=0):
    _select(browser, '', index=index)


def _set_id(browser: WebDriver, cell_id='foo', index=0):
    id_selector = '.nbgrader-CellId input'
    element = browser.find_elements_by_css_selector(id_selector)[index]
    element.clear()
    element.send_keys(cell_id)
    element.send_keys(Keys.ENTER)


def _set_points(browser: WebDriver, points=2, index=0):
    points_selector = '.nbgrader-CellPoints input'
    element = browser.find_elements_by_css_selector(points_selector)[index]
    element.clear()
    element.send_keys(str(points))
    element.send_keys(Keys.ENTER)


def _wait(browser: WebDriver):
    return WebDriverWait(browser, 30)


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

    time.sleep(1)
    _save_screenshot(browser)
