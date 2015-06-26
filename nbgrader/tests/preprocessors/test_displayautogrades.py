import pytest

try:
    from StringIO import StringIO # python 2
except ImportError:
    from io import StringIO # python 3

from textwrap import dedent
from IPython.nbformat.v4 import new_output

from nbgrader.preprocessors import DisplayAutoGrades
from nbgrader.tests.preprocessors.base import BaseTestPreprocessor
from nbgrader.tests import (
    create_code_cell, create_text_cell)

@pytest.fixture
def preprocessor():
    return DisplayAutoGrades()

@pytest.fixture
def stream():
    return StringIO()


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
