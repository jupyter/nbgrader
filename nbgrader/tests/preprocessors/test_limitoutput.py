import pytest

from textwrap import dedent
from nbgrader.preprocessors import LimitOutput
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import create_code_cell, create_text_cell


@pytest.fixture
def preprocessor():
    return LimitOutput()


class TestLimitOutput(BaseTestPreprocessor):

    def test_long_output(self):
        nb = self._read_nb("files/long-output.ipynb")
        cell, = nb.cells
        output, = cell.outputs
        assert len(output.text.split("\n")) > 1000

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        cell, = nb.cells
        output, = cell.outputs
        assert len(output.text.split("\n")) == 1000

    def test_infinite_recursion(self):
        nb = self._read_nb("files/infinite-recursion.ipynb")

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        cell, = nb.cells
        output, = cell.outputs
        assert len(output.traceback) == 100
