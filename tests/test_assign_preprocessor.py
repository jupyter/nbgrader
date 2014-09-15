import json
from IPython.nbformat.current import NotebookNode
from IPython.nbformat.current import new_code_cell, new_text_cell, new_notebook
from nose.tools import assert_raises
from nbgrader.preprocessors import Assign

from .base import TestBase


class TestAssign(TestBase):

    def setup(self):
        super(TestAssign, self).setup()
        self.preprocessor = Assign()

    def test_match_tests(self):
        """Are the tests matched to the correct problems?"""
        tests, rubric = self.preprocessor._match_tests(self.cells)
        assert tests == {
            "test1_for_problem1": {
                "weight": 0.3333333333333333,
                "points": 1,
                "problem": "problem1",
                "cell_type": "code"
            },
            "test2_for_problem1": {
                "weight": 0.6666666666666666,
                "points": 2,
                "problem": "problem1",
                "cell_type": "markdown"
            }
        }
        assert rubric == {
            "problem1": {
                "tests": ["test1_for_problem1", "test2_for_problem1"],
                "points": 3
            },
            "problem2": {
                "tests": [],
                "points": 0
            }
        }

    def test_match_tests_double_problem(self):
        """Is an error raised when a problem id is used twice?"""
        cell1 = new_code_cell()
        cell1.metadata = dict(nbgrader=dict(
            cell_type="grade", id="foo", points=""))
        cell2 = new_text_cell("markdown")
        cell2.metadata = dict(nbgrader=dict(
            cell_type="grade", id="foo", points=""))
        cells = [cell1, cell2]
        assert_raises(RuntimeError, self.preprocessor._match_tests, cells)

    def test_match_tests_no_match(self):
        """Is an error raised when an autograding cell cannot be matched?"""
        cell = new_code_cell()
        cell.metadata = dict(nbgrader=dict(
            cell_type="test"))
        cells = [cell]
        assert_raises(RuntimeError, self.preprocessor._match_tests, cells)

    def test_match_tests_double_test(self):
        """Is an error raised when a test id is used twice?"""
        cell1 = new_code_cell()
        cell1.metadata = dict(nbgrader=dict(
            cell_type="grade", id="foo", points=""))
        cell2 = new_code_cell()
        cell2.metadata = dict(nbgrader=dict(
            cell_type="test", id="foo_test"))
        cell3 = new_text_cell("markdown")
        cell3.metadata = dict(nbgrader=dict(
            cell_type="test", id="foo_test"))
        cells = [cell1, cell2, cell3]
        assert_raises(RuntimeError, self.preprocessor._match_tests, cells)

    def test_preprocess_nb_default_metadata(self):
        """Is the default metadata correctly set?"""
        nb, resources = self.preprocessor._preprocess_nb(self.nb, {})
        assert 'celltoolbar' not in nb.metadata
        assert nb.metadata['disable_nbgrader_toolbar']
        assert nb.metadata['hide_test_cells']

    def test_preprocess_nb_disable_toolbar(self):
        """Is the toolbar disabled?"""
        self.preprocessor.disable_toolbar = False
        nb, resources = self.preprocessor._preprocess_nb(self.nb, {})
        assert 'celltoolbar' not in nb.metadata
        assert not nb.metadata['disable_nbgrader_toolbar']
        assert nb.metadata['hide_test_cells']

    def test_preprocess_nb_hide_test_cells(self):
        """Are test cells hidden?"""
        self.preprocessor.hide_test_cells = False
        nb, resources = self.preprocessor._preprocess_nb(self.nb, {})
        assert 'celltoolbar' not in nb.metadata
        assert nb.metadata['disable_nbgrader_toolbar']
        assert not nb.metadata['hide_test_cells']

    def test_preprocess_test_cells_hide(self):
        """Are test cells properly preprocessed and hidden?"""
        self.preprocessor.hide_test_cells = True
        self.preprocessor.solution = False
        cell1 = self._create_code_cell()
        cell1.metadata = dict(nbgrader=dict(
            cell_type="grade", id="foo", points=1))
        cell2 = self._create_code_cell()
        cell2.input = "# hello"
        cell2.metadata = dict(nbgrader=dict(
            cell_type="test", id="foo"))
        cell3 = self._create_text_cell()
        cell3.source = "goodbye"
        cell3.metadata = dict(nbgrader=dict(
            cell_type="test", id="bar"))

        nb = new_notebook(worksheets=[NotebookNode()])
        nb.worksheets[0].cells = [cell1, cell2, cell3]

        nb, resources = self.preprocessor.preprocess(nb, {})
        cell1, cell2, cell3 = nb.worksheets[0].cells
        assert cell2.input == ""
        assert cell3.source == ""

        tests = resources['tests']
        assert tests == {
            "foo": dict(weight=0.5, points=0.5, problem="foo", source="# hello", cell_type="code"),
            "bar": dict(weight=0.5, points=0.5, problem="foo", source="goodbye", cell_type="markdown")
        }

    def test_preprocess_test_cells_show(self):
        """Are test cells properly preprocessed and shown?"""
        self.preprocessor.hide_test_cells = False
        self.preprocessor.solution = False
        cell1 = self._create_code_cell()
        cell1.metadata = dict(nbgrader=dict(
            cell_type="grade", id="foo", points=1))
        cell2 = self._create_code_cell()
        cell2.input = "# hello"
        cell2.metadata = dict(nbgrader=dict(
            cell_type="test", id="foo"))
        cell3 = self._create_text_cell()
        cell3.source = "goodbye"
        cell3.metadata = dict(nbgrader=dict(
            cell_type="test", id="bar"))

        nb = new_notebook(worksheets=[NotebookNode()])
        nb.worksheets[0].cells = [cell1, cell2, cell3]

        nb, resources = self.preprocessor.preprocess(nb, {})
        cell1, cell2, cell3 = nb.worksheets[0].cells
        assert cell2.input == "# hello"
        assert cell3.source == "goodbye"

        tests = resources['tests']
        assert tests == {
            "foo": dict(weight=0.5, points=0.5, problem="foo", source="# hello", cell_type="code"),
            "bar": dict(weight=0.5, points=0.5, problem="foo", source="goodbye", cell_type="markdown")
        }

    def test_extract_outputs_release(self):
        """Are outputs excluded in release version?"""
        self.preprocessor.solution = False
        nb, resources = self.preprocessor._preprocess_nb(self.nb, {})
        self.preprocessor._extract_outputs(resources)
        assert 'outputs' not in resources

    def test_extract_outputs_solution(self):
        """Are outputs include in solution version?"""
        self.preprocessor.solution = True
        nb, resources = self.preprocessor._preprocess_nb(self.nb, {})
        self.preprocessor._extract_outputs(resources)
        assert 'outputs' in resources

        rubric = json.dumps(resources['rubric'], indent=1)
        tests = json.dumps(resources['tests'], indent=1)
        assert resources['outputs']['rubric.json'] == rubric
        assert resources['outputs']['tests.json'] == tests

    def test_preprocess_solution(self):
        """Does the solution preprocessor succeed?"""
        self.preprocessor.solution = True
        self.preprocessor.preprocess(self.nb, {})

    def test_preprocess_release(self):
        """Does the release preprocessor succeed?"""
        self.preprocessor.solution = False
        self.preprocessor.preprocess(self.nb, {})
