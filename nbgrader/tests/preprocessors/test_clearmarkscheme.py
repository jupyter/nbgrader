import os
import pytest

from textwrap import dedent
from traitlets.config import Config

from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell, create_task_cell
from ...preprocessors import ClearMarkScheme


@pytest.fixture
def preprocessor():
    return ClearMarkScheme()


class TestClearMarkScheme(BaseTestPreprocessor):

    def test_remove_mark_scheme_region_code(self, preprocessor):
        """Are mark scheme regions in code cells correctly replaced?"""
        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert removed_test
        assert cell.source == "assert True"

    def test_remove_mark_scheme_region_no_end(self, preprocessor):
        """Is an error thrown when there is no end hidden test statement?"""
        source = dedent(
            """
            something something
            ### BEGIN MARK SCHEME
            this is a test!
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)

        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

    def test_remove_mark_scheme_region_nested_solution(self, preprocessor):
        """Is an error thrown when there are nested hidden test statements?"""
        source = dedent(
            """
            something something
            ### BEGIN MARK SCHEME
            ### BEGIN MARK SCHEME
            this is a test!
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)

        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

    def test_preprocess_code_cell_mark_scheme_region(self, preprocessor):
        """Is an error thrown when there is a mark region but it's not a task cell?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()
        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

    def test_preprocess_text_cell_metadata(self, preprocessor):
        """Is an error thrown when a mark scheme region exists in a non-task text cell?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()

        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

        # now disable enforcing metadata
        preprocessor.enforce_metadata = False
        cell, _ = preprocessor.preprocess_cell(cell, resources, 1)
        assert cell.source == "assert True"
        assert 'nbgrader' not in cell.metadata

    def test_dont_remove_mark_scheme_region(self, preprocessor):
        """Is false returned when there is no hidden test region?"""
        source = "nothing to remove"
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert not removed_test

    def test_preprocess_notebook(self, preprocessor):
        """Is the test notebook processed without error?"""
        nb = self._read_nb(os.path.join("files", "test_taskcell.ipynb"))
        preprocessor.preprocess(nb, {})

    # attachment detection tests
    def test_attachment_in_mark_scheme(self, preprocessor):
        """Is an error raised when there is an attachment in the marking scheme?"""
        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            ![](attachment:image.png)
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            ![alt text](attachment:answers.png)
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            Text text text text text.
            ![](attachment:image1.jpg)
            Grade grade grade.
            ![](attachment:image2.png)
            Mark mark mark mark.
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

    def test_attachment_suppress_error(self, preprocessor):
        """Can the error be suppressed?"""
        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            ![](attachment:image.png)
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        preprocessor.check_attachment_leakage = False
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert removed_test
        assert cell.source == "assert True"

    def test_attachment_not_in_mark_scheme(self, preprocessor):
        """Attachments outside of marking schemes shouldn't be touched"""
        source = dedent(
            """
            ![](attachment:image.png)
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, 'markdown', 'some-task-id', 2)
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert removed_test
        assert cell.source == "![](attachment:image.png)"
