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
            'metadata': {'path': 'nbgrader/docs/source/user_guide'}
        }
        preprocessor._load_test_template_file(resources=resources)
        assert preprocessor.test_templates_by_type is not None
        assert preprocessor.dispatch_template is not None
        assert preprocessor.success_code is not None
        assert preprocessor.hash_template is not None
        assert preprocessor.check_template is not None
        assert preprocessor.normalize_template is not None
        assert preprocessor.setup_code is not None

    def test_has_sanitizers(self, preprocessor):
        assert 'python' in preprocessor.sanitizers.keys()
        assert 'python3' in preprocessor.sanitizers.keys()
        assert 'ir' in preprocessor.sanitizers.keys()

    def test_has_comment_strs(self, preprocessor):
        assert 'python' in preprocessor.comment_strs.keys()
        assert 'python3' in preprocessor.comment_strs.keys()
        assert 'ir' in preprocessor.comment_strs.keys()

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

    # test that a warning is thrown when we set enforce_metadata = False and have an AUTOTEST directive in a non-grade cell
    def test_warning_autotest_nongrade(self, preprocessor):
        pass

    # test that an error is thrown when we have an AUTOTEST directive in a non-grade cell
    def test_error_autotest_nongrade(self, preprocessor):
        pass

    # test that AUTOTEST directives are not removed from non-grade cells (and that all non-grade cells are not modified)
    def test_no_remove_autotest_nongrade(self, preprocessor):
        pass

    # test that invalid python statements in AUTOTEST directives cause errors
    def test_error_bad_autotest_code(self, preprocessor):
        pass

    # test the code generated for some basic types; ensure correct solution gives success, a few wrong solns give failures
    def test_int_autotest(self, preprocessor):
        pass

    def test_float_autotest(self, preprocessor):
        pass

    def test_string_autotest(self, preprocessor):
        pass

    def test_list_autotest(self, preprocessor):
        pass

