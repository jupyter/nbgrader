import pytest
import os

from ...preprocessors import IgnorePattern
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessor():
    pp = IgnorePattern()
    pp.pattern = r"\[.*\.cpp.*\] Could not initialize NNPACK! Reason: Unsupported hardware."
    return pp


class TestIgnorePattern(BaseTestPreprocessor):

    def test_remove_matching_output(self, preprocessor):
        nb = self._read_nb(os.path.join("files", "warning-pattern.ipynb"))
        cell = nb.cells[0]
        
        outputs = cell.outputs
        assert len(outputs) == 2

        cell, _ = preprocessor.preprocess_cell(cell, {}, 0)

        assert len(cell.outputs) == 1


    def test_skip_nonmatching_output(self, preprocessor):
        nb = self._read_nb(os.path.join("files", "warning-pattern.ipynb"))
        cell = nb.cells[1]
        
        outputs = cell.outputs
        assert len(outputs) == 1

        cell, _ = preprocessor.preprocess_cell(cell, {}, 1)

        assert len(cell.outputs) == 1
        assert cell.outputs[0].name == "stderr"

