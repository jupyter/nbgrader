import pytest
import os
from textwrap import dedent
from ...preprocessors import LimitTestCellHeights
from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell
from nbformat.v4 import new_notebook


@pytest.fixture
def preprocessor():
    return LimitTestCellHeights()


class TestLimitTestCellHeights(BaseTestPreprocessor):

    def test_replace_autotest_code(self, preprocessor):
        test_cell = create_code_cell()
        test_cell.metadata['nbgrader'] = {'grade': True}
        resources = dict()
        cell = preprocessor.preprocess_cell(test_cell, resources, 1)[0]
        assert cell.metadata['max_height']

