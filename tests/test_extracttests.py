import json
from IPython.nbformat.current import NotebookNode
from IPython.nbformat.current import new_code_cell, new_text_cell, new_notebook
from nose.tools import assert_raises
from nbgrader.preprocessors import ExtractTests

from .base import TestBase


class TestExtractTests(TestBase):

    def setup(self):
        super(TestExtractTests, self).setup()
        self.preprocessor = ExtractTests()

    def test_match_tests(self):
        """Are the tests matched to the correct problems?"""
        tests, rubric = self.preprocessor._match_tests(self.nb)
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
        self.nb.worksheets[0].cells = [cell1, cell2]
        assert_raises(RuntimeError, self.preprocessor._match_tests, self.nb)

    def test_match_tests_no_match(self):
        """Is an error raised when an autograding cell cannot be matched?"""
        cell = new_code_cell()
        cell.metadata = dict(nbgrader=dict(
            cell_type="test"))
        self.nb.worksheets[0].cells = [cell]
        assert_raises(RuntimeError, self.preprocessor._match_tests, self.nb)

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
        self.nb.worksheets[0].cells = [cell1, cell2, cell3]
        assert_raises(RuntimeError, self.preprocessor._match_tests, self.nb)

    def test_extract_outputs_solution(self):
        """Are outputs included?"""
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert 'outputs' in resources

        rubric = json.dumps(resources['rubric'], indent=1)
        tests = json.dumps(resources['tests'], indent=1)
        assert resources['outputs']['rubric.json'] == rubric
        assert resources['outputs']['tests.json'] == tests
