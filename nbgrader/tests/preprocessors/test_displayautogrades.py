import pytest
import json
import six
import os

from textwrap import dedent
from nbformat.v4 import new_output

from ...preprocessors import DisplayAutoGrades
from .base import BaseTestPreprocessor
from .. import (
    create_code_cell, create_text_cell)

@pytest.fixture
def preprocessor():
    return DisplayAutoGrades()

@pytest.fixture
def stream():
    return six.StringIO()


class TestDisplayAutoGrades(BaseTestPreprocessor):

    def _add_error(self, cell):
        cell.outputs.append(new_output(
            "error",
            ename="Error",
            evalue="oh noes, an error occurred!",
            traceback=["oh noes, an error occurred!"]
        ))
        return cell

    def test_indent(self, preprocessor):
        # test normal indenting
        assert preprocessor._indent("Hello, world!") == "    Hello, world!"
        assert preprocessor._indent("Hello,\n world!") == "    Hello,\n     world!"

        # test truncation
        preprocessor.width = 10
        assert preprocessor._indent("Hello, world!") == "    Hel..."
        assert preprocessor._indent("Hello,\n world!") == "    Hel...\n     wo..."

        # test that ansi escape sequences are removed and not counted towards
        # the line width
        assert preprocessor._indent("\x1b[30mHello, world!\x1b[0m") == "    Hel..."
        assert preprocessor._indent("\x1b[30mHello,\n world!\x1b[0m") == "    Hel...\n     wo..."

    def test_print_changed(self, preprocessor, stream):
        cell = create_code_cell()
        preprocessor.stream = stream
        preprocessor.width = 20
        preprocessor._print_changed(cell)

        expected = dedent(
            """
            ====================
            The following cell has changed:

                print("someth...
                ### BEGIN SOL...
                print("hello"...
                ### END SOLUT...

            """
        )

        assert stream.getvalue() == expected

    def test_print_error_code_cell(self, preprocessor, stream):
        cell = create_code_cell()
        preprocessor.stream = stream
        preprocessor.width = 20
        preprocessor._print_error(cell)

        expected = dedent(
            """
            ====================
            The following cell failed:

                print("someth...
                ### BEGIN SOL...
                print("hello"...
                ### END SOLUT...

            The error was:

                You did not p...

            """
        )

        assert stream.getvalue() == expected

    def test_print_error_code_cell_error(self, preprocessor, stream):
        cell = self._add_error(create_code_cell())
        preprocessor.stream = stream
        preprocessor.width = 20
        preprocessor._print_error(cell)

        expected = dedent(
            """
            ====================
            The following cell failed:

                print("someth...
                ### BEGIN SOL...
                print("hello"...
                ### END SOLUT...

            The error was:

                oh noes, an e...

            """
        )

        assert stream.getvalue() == expected

    def test_print_error_markdown_cell(self, preprocessor, stream):
        cell = create_text_cell()
        preprocessor.stream = stream
        preprocessor.width = 20
        preprocessor._print_error(cell)

        expected = dedent(
            """
            ====================
            The following cell failed:

                this is the a...

            The error was:

                You did not p...

            """
        )

        assert stream.getvalue() == expected

    def test_print_pass(self, preprocessor, stream):
        cell = create_code_cell()
        preprocessor.stream = stream
        preprocessor.width = 20
        preprocessor._print_pass(cell)

        expected = dedent(
            """
            ====================
            The following cell passed:

                print("someth...
                ### BEGIN SOL...
                print("hello"...
                ### END SOLUT...

            """
        )

        assert stream.getvalue() == expected

    def test_print_num_changed_0(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_changed(0)
        assert stream.getvalue() == ""

    def test_print_num_changed_1(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_changed(1)
        assert stream.getvalue().startswith("THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED!")

    def test_print_num_failed(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_failed(0)
        assert stream.getvalue() == "Success! Your notebook passes all the tests.\n"

    def test_print_num_failed_1(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_failed(1)
        assert stream.getvalue().startswith("VALIDATION FAILED ON 1 CELL(S)!")

    def test_print_num_passed(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_passed(0)
        assert stream.getvalue() == "Success! The notebook does not pass any tests.\n"

    def test_print_num_passed_1(self, preprocessor, stream):
        preprocessor.stream = stream
        preprocessor._print_num_passed(1)
        assert stream.getvalue().startswith("NOTEBOOK PASSED ON 1 CELL(S)!")

    def test_submitted_unchanged(self, preprocessor, stream):
        """Does the validation fail on an unchanged notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "VALIDATION FAILED ON 3 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_submitted_changed(self, preprocessor, stream):
        """Does the validation pass on an changed notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.preprocess(nb, {})
        assert stream.getvalue() == "Success! Your notebook passes all the tests.\n"

    def test_invert_submitted_unchanged(self, preprocessor, stream):
        """Does the inverted validation pass on an unchanged notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "NOTEBOOK PASSED ON 1 CELL(S)!"

    def test_invert_submitted_changed(self, preprocessor, stream):
        """Does the inverted validation fail on a changed notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_grade_cell_changed(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_grade_cell_changed_ignore_checksums(self, preprocessor, stream):
        """Does the validate pass if a grade cell has changed but we're ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "Success! Your notebook passes all the tests."

    def test_invert_grade_cell_changed(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed, even with --invert?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_invert_grade_cell_changed_ignore_checksums(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed with --invert and ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_submitted_unchanged_ignore_checksums(self, preprocessor, stream):
        """Does the validation fail on an unchanged notebook with ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "VALIDATION FAILED ON 1 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_locked_cell_changed(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "THE CONTENTS OF 2 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_locked_cell_changed_ignore_checksums(self, preprocessor, stream):
        """Does the validate pass if a locked cell has changed but we're ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "VALIDATION FAILED ON 1 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_invert_locked_cell_changed(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed, even with --invert?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "THE CONTENTS OF 2 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_invert_locked_cell_changed_ignore_checksums(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed with --invert and ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.invert = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        assert stream.getvalue().split("\n")[0] == "NOTEBOOK PASSED ON 1 CELL(S)!"

    def test_submitted_unchanged_json(self, preprocessor, stream):
        """Does the validation fail on an unchanged notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["failed"]
        assert len(output["failed"]) == 3
        assert output["failed"][0]["source"] == "assert a == 1"
        assert output["failed"][1]["source"] == "YOUR ANSWER HERE"
        assert output["failed"][1]["error"] == "You did not provide a response."
        assert output["failed"][2]["source"] == "# YOUR CODE HERE\nraise NotImplementedError()"

    def test_submitted_changed_json(self, preprocessor, stream):
        """Does the validation pass on an changed notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == []

    def test_invert_submitted_unchanged_json(self, preprocessor, stream):
        """Does the inverted validation pass on an unchanged notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["passed"]
        assert len(output["passed"]) == 1
        assert output["passed"][0]["source"] == 'print("Success!")'

    def test_invert_submitted_changed_json(self, preprocessor, stream):
        """Does the inverted validation fail on a changed notebook?"""
        nb = self._read_nb(os.path.join("files", "submitted-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["passed"]
        assert len(output["passed"]) == 2
        assert output["passed"][0]["source"] == 'print("Success!")'
        assert output["passed"][1]["source"] == 'assert a == 1'

    def test_grade_cell_changed_json(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["changed"]
        assert len(output["changed"]) == 1
        assert output["changed"][0]["source"] == '#assert a == 1'

    def test_grade_cell_changed_ignore_checksums_json(self, preprocessor, stream):
        """Does the validate pass if a grade cell has changed but we're ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == []

    def test_invert_grade_cell_changed_json(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed, even with --invert?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["changed"]
        assert len(output["changed"]) == 1
        assert output["changed"][0]["source"] == '#assert a == 1'

    def test_invert_grade_cell_changed_ignore_checksums_json(self, preprocessor, stream):
        """Does the validate fail if a grade cell has changed with --invert and ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-grade-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["passed"]
        assert len(output["passed"]) == 2
        assert output["passed"][0]["source"] == 'print("Success!")'
        assert output["passed"][1]["source"] == '#assert a == 1'

    def test_submitted_unchanged_ignore_checksums_json(self, preprocessor, stream):
        """Does the validation fail on an unchanged notebook with ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-unchanged.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["failed"]
        assert len(output["failed"]) == 1
        assert output["failed"][0]["source"] == 'assert a == 1'

    def test_locked_cell_changed_json(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["changed"]
        assert len(output["changed"]) == 2
        assert output["changed"][0]["source"] == '#print("Don\'t change this cell!")'
        assert output["changed"][1]["source"] == "This cell shouldn't \nbe changed."

    def test_locked_cell_changed_ignore_checksums_json(self, preprocessor, stream):
        """Does the validate pass if a locked cell has changed but we're ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["failed"]
        assert len(output["failed"]) == 1
        assert output["failed"][0]["source"] == 'assert a == 1'

    def test_invert_locked_cell_changed_json(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed, even with --invert?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["changed"]
        assert len(output["changed"]) == 2
        assert output["changed"][0]["source"] == '#print("Don\'t change this cell!")'
        assert output["changed"][1]["source"] == "This cell shouldn't \nbe changed."

    def test_invert_locked_cell_changed_ignore_checksums_json(self, preprocessor, stream):
        """Does the validate fail if a locked cell has changed with --invert and ignoring checksums?"""
        nb = self._read_nb(os.path.join("files", "submitted-locked-cell-changed.ipynb"))
        preprocessor.stream = stream
        preprocessor.as_json = True
        preprocessor.invert = True
        preprocessor.ignore_checksums = True
        preprocessor.preprocess(nb, {})
        output = json.loads(stream.getvalue())
        assert list(output.keys()) == ["passed"]
        assert len(output["passed"]) == 1
        assert output["passed"][0]["source"] == 'print("Success!")'
