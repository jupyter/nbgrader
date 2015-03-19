import subprocess as sp
import tempfile
import os
import shutil

from nose.tools import assert_equal

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

class TestCreateAssignmentNbExtension(object):

    def setup(self):
        self.tempdir = tempfile.mkdtemp()
        self.ipythondir = tempfile.mkdtemp()
        self.origdir = os.getcwd()
        os.chdir(self.tempdir)
        shutil.copy(os.path.join(os.path.dirname(__file__), "files", "blank.ipynb"), "blank.ipynb")

        self.nbserver = sp.Popen([
            "ipython", "notebook",
            "--ipython-dir", self.ipythondir,
            "--no-browser",
            "--port", "9000"])#, stdout=sp.PIPE, stderr=sp.STDOUT)
        self.browser = webdriver.PhantomJS()
        self.browser.get("http://localhost:9000/notebooks/blank.ipynb")

    def teardown(self):
        self.browser.quit()
        self.nbserver.kill()

        os.chdir(self.origdir)
        shutil.rmtree(self.tempdir)
        shutil.rmtree(self.ipythondir)

    def test_create_assignment(self):
        # wait for the celltoolbar menu to appear
        element = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctb_select')))

        # load the nbextension
        self.browser.execute_script("IPython.load_extensions('nbgrader')")

        # activate the Create Assignment toolbar
        select = Select(element)
        select.select_by_visible_text("Create Assignment")

        # wait for the toolbar(s) to appear
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".celltoolbar input")))
        assert_equal(element[0].get_attribute("type"), "checkbox")

        # does the nbgrader metadata exist?
        metadata = self.browser.execute_script("return IPython.notebook.get_cell(0).metadata.nbgrader")
        assert_equal(metadata, {})

        # click the "solution?" checkbox
        solution = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[3]).find("input").click();
            return cell.metadata.nbgrader.solution;
            """
        )
        assert solution

        # unclick the "solution?" checkbox
        solution = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[3]).find("input").click();
            return cell.metadata.nbgrader.solution;
            """
        )
        assert not solution

        # click the "grade?" checkbox
        grade = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            return cell.metadata.nbgrader.grade;
            """
        )
        assert grade

        # wait for the points and id fields to appear
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-points")))
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nbgrader-id")))

        # set the points
        points = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-points-input");
            elem.val("2");
            elem.trigger("change");
            return cell.metadata.nbgrader.points;
            """
        )
        assert_equal(points, 2)

        # set the id
        grade_id = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-id-input");
            elem.val("foo");
            elem.trigger("change");
            return cell.metadata.nbgrader.grade_id;
            """
        )
        assert_equal(grade_id, "foo")

        # unclick the "grade?" checkbox
        metadata = self.browser.execute_script(
            """
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            return cell.metadata.nbgrader;
            """
        )
        assert not metadata['grade']
