import subprocess as sp
import tempfile
import os
import shutil
from copy import copy

from nose.tools import assert_equal

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from nbgrader.install import main


class TestCreateAssignmentNbExtension(object):

    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.ipythondir = tempfile.mkdtemp()
        cls.origdir = os.getcwd()
        os.chdir(cls.tempdir)

        # ensure IPython dir exists.
        sp.call([
            'ipython', 'profile', 'create', '--ipython-dir', cls.ipythondir])

        # test the arg parsing
        main(['--activate',
              '--verbose',
              '--path={}'.format(cls.ipythondir),
              'default'])

        # bug in IPython cannot use --profile-dir
        # that does not set it for everything. 
        # still this does not allow to have things that work.
        env = copy(os.environ)
        env['IPYTHONDIR'] = cls.ipythondir

        cls.nbserver = sp.Popen([
            "ipython", "notebook",
            "--no-browser",
            "--port", "9000"], stdout=sp.PIPE, stderr=sp.STDOUT
            ,env=env
            )

    @classmethod
    def teardown_class(cls):
        cls.nbserver.kill()

        os.chdir(cls.origdir)
        shutil.rmtree(cls.tempdir)
        shutil.rmtree(cls.ipythondir)

    def setup(self):
        shutil.copy(os.path.join(os.path.dirname(__file__), "files", "blank.ipynb"), "blank.ipynb")
        self.browser = webdriver.PhantomJS()
        self.browser.get("http://localhost:9000/notebooks/blank.ipynb")

    def teardown(self):
        self.browser.quit()

    def _load_extension(self):
        # wait for the celltoolbar menu to appear
        WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctb_select')))

        # load the nbextension
        self.browser.execute_script("IPython.load_extensions('nbgrader/nbgrader')")

    def _activate_toolbar(self, name="Create Assignment"):
        # activate the Create Assignment toolbar
        element = self.browser.find_element_by_css_selector("#ctb_select")
        select = Select(element)
        select.select_by_visible_text(name)


    def _click_solution(self):
        self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[3]).find("input").click();
            """
        )

    def _click_grade(self):        
        self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            """
        )

    def _set_points(self):
        self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-points-input");
            elem.val("2");
            elem.trigger("change");
            """
        )

    def _set_grade_id(self):
        self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-id-input");
            elem.val("foo");
            elem.trigger("change");
            """
        )

    def _get_metadata(self):
        return self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            return cell.metadata.nbgrader;
            """
        )

    def test_create_assignment(self):
        self._load_extension()
        self._activate_toolbar()

        # make sure the toolbar appeared
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar input")))
        assert_equal(element[0].get_attribute("type"), "checkbox")

        # does the nbgrader metadata exist?
        assert_equal({}, self._get_metadata())

        # click the "solution?" checkbox
        self._click_solution()
        assert self._get_metadata()['solution']

        # unclick the "solution?" checkbox
        self._click_solution()
        assert not self._get_metadata()['solution']

        # click the "grade?" checkbox
        self._click_grade()
        assert self._get_metadata()['grade']

        # wait for the points and id fields to appear
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-points")))
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

        # set the points
        self._set_points()
        assert_equal(2, self._get_metadata()['points'])

        # set the id
        self._set_grade_id()
        assert_equal("foo", self._get_metadata()['grade_id'])

        # unclick the "grade?" checkbox
        self._click_grade()
        assert not self._get_metadata()['grade']

    def test_grade_cell_css(self):
        self._load_extension()
        self._activate_toolbar()

        # click the "grade?" checkbox
        self._click_grade()
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 1)

        # unclick the "grade?" checkbox
        self._click_grade()
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 0)

        # click the "grade?" checkbox
        self._click_grade()
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 1)

        # deactivate the toolbar
        self._activate_toolbar("None")
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 0)

        # activate the toolbar
        self._activate_toolbar()
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 1)

        # deactivate the toolbar
        self._activate_toolbar("Edit Metadata")
        elements = self.browser.find_elements_by_css_selector(".nbgrader-grade-cell")
        assert_equal(len(elements), 0)

    def test_tabbing(self):
        self._load_extension()
        self._activate_toolbar()

        # click the "grade?" checkbox
        self._click_grade()

        # click the id field
        element = self.browser.find_element_by_css_selector(".nbgrader-id-input")
        element.click()

        # get the active element
        element = self.browser.execute_script("return document.activeElement")
        assert_equal("nbgrader-id-input", element.get_attribute("class"))

        # press tab and check that the active element is correct
        element.send_keys(Keys.TAB)
        element = self.browser.execute_script("return document.activeElement")
        assert_equal("nbgrader-points-input", element.get_attribute("class"))
