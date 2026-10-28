import pytest
import os

from textwrap import dedent
from nbformat.v4 import new_output
from ...preprocessors import LimitOutput
from ...utils import determine_grade, has_failed
from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell, create_grade_cell


@pytest.fixture
def preprocessor():
    return LimitOutput()


class TestLimitOutput(BaseTestPreprocessor):

    @pytest.mark.parametrize("stdout_lines", [998, 999, 1000, 1200])
    def test_stderr_after_long_stdout_preserves_failure(self, stdout_lines):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n" * stdout_lines),
            new_output("stream", name="stderr", text="test failed\n"),
        ]

        cell, _ = LimitOutput().preprocess_cell(cell, {}, 0)

        assert any(output.name == "stderr" for output in cell.outputs)
        assert has_failed(cell)
        assert determine_grade(cell) == (0, 10.0)

    def test_stderr_after_separate_stdout_outputs_preserves_failure(self):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n")
            for _ in range(500)
        ] + [new_output("stream", name="stderr", text="test failed\n")]

        cell, _ = LimitOutput().preprocess_cell(cell, {}, 0)

        assert has_failed(cell)
        assert determine_grade(cell) == (0, 10.0)

    @pytest.mark.parametrize("max_lines", [0, 1, 3])
    def test_repeated_stderr_after_limit_is_bounded(self, max_lines):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n" * 10)
        ] + [
            new_output("stream", name="stderr", text="test failed\n")
            for _ in range(20)
        ]

        cell, _ = LimitOutput(max_lines=max_lines).preprocess_cell(cell, {}, 0)

        stderr = [output for output in cell.outputs if output.name == "stderr"]
        assert len(stderr) == 1
        assert stderr[0].text == "... Output truncated ..."
        assert sum(len(output.text.split("\n")) for output in cell.outputs) <= max_lines + 1
        assert determine_grade(cell) == (0, 10.0)

    def test_stdout_only_after_limit_remains_truncated(self):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n" * 10),
            new_output("stream", name="stdout", text="more output\n"),
        ]

        cell, _ = LimitOutput(max_lines=3).preprocess_cell(cell, {}, 0)

        assert len(cell.outputs) == 1
        assert len(cell.outputs[0].text.split("\n")) == 3
        assert determine_grade(cell) == (10.0, 10.0)

    def test_unlimited_stream_output_is_unchanged(self):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n" * 1200),
            new_output("stream", name="stderr", text="test failed\n"),
        ]
        original_outputs = [dict(output) for output in cell.outputs]

        cell, _ = LimitOutput(max_lines=-1).preprocess_cell(cell, {}, 0)

        assert cell.outputs == original_outputs
        assert determine_grade(cell) == (0, 10.0)

    def test_error_output_after_limit_preserves_failure(self):
        cell = create_grade_cell("", "code", "test", 10)
        cell.outputs = [
            new_output("stream", name="stdout", text="line\n" * 1200),
            new_output("error", ename="AssertionError", evalue="failed", traceback=[]),
        ]

        cell, _ = LimitOutput().preprocess_cell(cell, {}, 0)

        assert cell.outputs[-1].output_type == "error"
        assert has_failed(cell)
        assert determine_grade(cell) == (0, 10.0)

    def test_long_output(self):
        nb = self._read_nb(os.path.join("files", "long-output.ipynb"))
        cell, = nb.cells
        output, = cell.outputs
        assert len(output.text.split("\n")) > 1000

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        cell, = nb.cells
        output, = cell.outputs
        assert len(output.text.split("\n")) == 1000

    def test_infinite_recursion(self):
        nb = self._read_nb(os.path.join("files", "infinite-recursion.ipynb"))

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        cell, = nb.cells
        output, = cell.outputs
        assert len(output.traceback) == 100
