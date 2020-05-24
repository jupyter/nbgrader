import time

import pytest
from selenium.common.exceptions import (NoAlertPresentException,
                                        NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .conftest import (_close_browser, _close_nbserver, _make_browser,
                       _make_nbserver)


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir,
             exchange, cache):
    server = _make_nbserver("", port, tempdir, jupyter_config_dir,
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


def _click_element(browser: WebDriver, element):
    ActionChains(browser).click(element).perform()


def _click_validate_button(browser: WebDriver):
    selector = '.jp-NotebookPanel:not(.lm-mod-hidden) button.validate-button'
    browser.find_element_by_css_selector(selector).click()


def _click_when_available(browser: WebDriver, by, arg):
    _wait(browser).until(lambda x: browser.find_element(by, arg))
    element = browser.find_element(by, arg)
    _wait(browser).until(EC.visibility_of(element))
    _click_element(browser, element)
    return element


def _dismiss_modal(browser: WebDriver):
    selector = '.jp-Dialog button.jp-mod-accept'
    accept_button = browser.find_element_by_css_selector(selector)
    accept_button.click()
    _wait(browser).until(EC.staleness_of(accept_button))


def _find_element_by_modal_class(browser: WebDriver, class_name: str):
    selector = '.jp-Dialog .' + class_name
    return browser.find_element_by_css_selector(selector)


def _get_element(browser: WebDriver, css_selector):
    try:
        return browser.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        return None


def _get_kernel(browser: WebDriver):
    kernel_selector = '.jp-NotebookPanel:not(.lm-mod-hidden) .jp-KernelName'
    _wait(browser).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, kernel_selector)))
    kernel_element = _get_element(browser, kernel_selector)
    return kernel_element.text


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
    file_class = 'lm-MenuBar-item'
    open_from_path_selector = '.lm-Menu-item' \
                              + '[data-command="filebrowser:open-path"]'
    path_input_selector = '.jp-Input-Dialog input'

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
    _wait(browser).until(EC.staleness_of(open_element))
    _wait(browser).until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, active_tab_label_selector),
            '{}.ipynb'.format(name)))
    if expect_schema_modal:
        _wait_for_modal(browser, title='Outdated schema version')
        _dismiss_modal(browser)
    if 'Kernel' == _get_kernel(browser):
        select_element = _click_when_available(browser, By.CLASS_NAME,
                                               accept_selector)
        _wait(browser).until(EC.staleness_of(select_element))


def _wait(browser):
    return WebDriverWait(browser, 30)


def _wait_for_modal(browser: WebDriver, title=None):
    class_name = 'jp-Dialog'
    condition = EC.presence_of_element_located((
            By.CLASS_NAME, class_name))
    element = _wait(browser).until(condition)
    if title is not None:
        header_class = 'jp-Dialog-header'
        header_text = element.find_element_by_class_name(header_class).text
        assert title == header_text


def _wait_for_validate_button(browser):
    selector = '.jp-NotebookPanel:not(.lm-mod-hidden) button.validate-button'
    _wait(browser).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                         selector)))


@pytest.mark.labextensions
def test_validate_ok(browser, port):
    _load_notebook(browser, port, name="submitted-changed")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    _find_element_by_modal_class(browser, 'validation-success')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_failure(browser, port):
    _load_notebook(browser, port, name="submitted-unchanged")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    _find_element_by_modal_class(browser, 'validation-failed')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_grade_cell_changed(browser, port):
    _load_notebook(browser, port, name="submitted-grade-cell-changed")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    _find_element_by_modal_class(browser, 'validation-changed')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_locked_cell_changed(browser, port):
    _load_notebook(browser, port, name="submitted-locked-cell-changed")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    _find_element_by_modal_class(browser, 'validation-changed')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_open_relative_file(browser, port):
    _load_notebook(browser, port, name="open_relative_file")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    _find_element_by_modal_class(browser, 'validation-success')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_grade_cell_type_changed(browser, port):
    _load_notebook(browser, port, name="submitted-grade-cell-type-changed")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    _find_element_by_modal_class(browser, 'validation-type-changed')

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.labextensions
def test_validate_answer_cell_type_changed(browser, port):
    _load_notebook(browser, port, name="submitted-answer-cell-type-changed")
    _wait_for_validate_button(browser)

    # click the "validate" button
    _click_validate_button(browser)

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    _find_element_by_modal_class(browser, 'validation-type-changed')

    # close the modal dialog
    _dismiss_modal(browser)
