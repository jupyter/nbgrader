import pytest
import os
from textwrap import dedent
from ...preprocessors import InstantiateTests
from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell, create_autotest_solution_cell, create_autotest_test_cell
from nbformat.v4 import new_notebook


@pytest.fixture
def preprocessor():
    return InstantiateTests()


class TestInstantiateTests(BaseTestPreprocessor):

    def test_load_test_template_file(self, preprocessor):
        resources = {
            'kernel_name': 'python3',
            'metadata': {'path': 'nbgrader/docs/source/user_guide/'}
        }
        preprocessor._load_test_template_file(resources=resources)
        assert preprocessor.test_templates_by_type is not None
        assert preprocessor.dispatch_template is not None
        assert preprocessor.success_code is not None
        assert preprocessor.hash_template is not None
        assert preprocessor.check_template is not None
        assert preprocessor.normalize_template is not None
        assert preprocessor.setup_code is not None

    def test_replace_autotest_code(self, preprocessor):
        sol_cell = create_autotest_solution_cell()
        test_cell = create_autotest_test_cell()
        test_cell.metadata['nbgrader'] = {'grade': True}
        nb = new_notebook()
        nb.metadata['kernelspec'] = {
            "name": "python3"
        }
        nb.cells.append(sol_cell)
        nb.cells.append(test_cell)
        resources = {
            'metadata': {'path': 'nbgrader/docs/source/user_guide/'}
        }
        nb, resources = preprocessor.preprocess(nb, resources)
        assert 'assert' in nb['cells'][1]['source']

