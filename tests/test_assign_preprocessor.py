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

    def test_preprocess_solution(self):
        """Does the solution preprocessor succeed?"""
        self.preprocessor.solution = True
        self.preprocessor.preprocess(self.nb, {})

    def test_preprocess_release(self):
        """Does the release preprocessor succeed?"""
        self.preprocessor.solution = False
        self.preprocessor.preprocess(self.nb, {})
