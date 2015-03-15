import traceback
from nose.tools import assert_raises, assert_equal
from textwrap import dedent
from nbgrader.preprocessors import ClearSolutions

from .base import TestBase


class TestClearSolutions(TestBase):

    def setup(self):
        super(TestClearSolutions, self).setup()
        self.preprocessor = ClearSolutions()

    def test_custom_solution_region(self):
        """Are the solution region delimeters properly formatted?"""
        pp = ClearSolutions(
            comment_mark="%",
            begin_solution_delimeter="!!foo",
            end_solution_delimeter="@@bar")
        assert_equal(pp.begin_solution, "%!!foo")
        assert_equal(pp.end_solution, "%@@bar")

    def test_replace_solution_region_code(self):
        """Are solution regions in code cells correctly replaced?"""
        cell = self._create_code_cell()
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert_equal(
            cell.source,
            dedent(
                """
                print("something")
                # YOUR CODE HERE
                raise NotImplementedError()
                """
            ).strip()
        )

    def test_replace_solution_region_text(self):
        """Are solution regions in text cells correctly replaced?"""
        cell = self._create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert_equal(cell.source, "something something\nYOUR ANSWER HERE")

    def test_dont_replace_solution_region(self):
        """Is false returned when there is no solution region?"""
        cell = self._create_text_cell()
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert not replaced_solution

    def test_replace_solution_region_no_end(self):
        """Is an error thrown when there is no end solution statement?"""
        cell = self._create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            """
        ).strip()
        assert_raises(
            RuntimeError, self.preprocessor._replace_solution_region, cell)

    def test_replace_solution_region_nested_solution(self):
        """Is an error thrown when there are nested solution statements?"""
        cell = self._create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()
        assert_raises(
            RuntimeError, self.preprocessor._replace_solution_region, cell)

    def test_preprocess_code_cell_student(self):
        """Is the student version of a code cell correctly preprocessed?"""
        cell = self._create_code_cell()

        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert_equal(
            cell.source,
            dedent(
                """
                print("something")
                # YOUR CODE HERE
                raise NotImplementedError()
                """
            ).strip()
        )

    def test_preprocess_code_solution_cell_solution_region(self):
        """Is a code solution cell correctly cleared when there is a solution region?"""
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = dict(solution=True)
        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert_equal(
            cell.source,
            dedent(
                """
                print("something")
                # YOUR CODE HERE
                raise NotImplementedError()
                """
            ).strip()
        )
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_cell_solution_region(self):
        """Is a code cell correctly cleared when there is a solution region?"""
        cell = self._create_code_cell()
        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert_equal(
            cell.source,
            dedent(
                """
                print("something")
                # YOUR CODE HERE
                raise NotImplementedError()
                """
            ).strip()
        )
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_solution_cell_no_region(self):
        """Is a code solution cell correctly cleared when there is no solution region?"""
        cell = self._create_code_cell()
        cell.source = """print("the answer!")"""
        cell.metadata['nbgrader'] = dict(solution=True)

        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert_equal(
            cell.source,
            dedent(
                """
                # YOUR CODE HERE
                raise NotImplementedError()
                """
            ).strip()
        )

        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_cell_no_region(self):
        """Is a code cell not cleared when there is no solution region?"""
        cell = self._create_code_cell()
        cell.source = """print("the answer!")"""
        cell.metadata['nbgrader'] = dict()
        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert_equal(cell.source, """print("the answer!")""")
        assert not cell.metadata.nbgrader.get('solution', False)

    def test_preprocess_text_solution_cell_no_region(self):
        """Is a text grade cell correctly cleared when there is no solution region?"""
        cell = self._create_text_cell()
        cell.metadata['nbgrader'] = dict(solution=True)
        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert_equal(cell.source, "YOUR ANSWER HERE")
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_text_cell_no_region(self):
        """Is a text grade cell correctly cleared when there is no solution region?"""
        cell = self._create_text_cell()
        cell.metadata['nbgrader'] = dict()
        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert_equal(cell.source, "this is the answer!\n")
        assert not cell.metadata.nbgrader.get('solution', False)

    def test_preprocess_text_solution_cell_region(self):
        """Is a text grade cell correctly cleared when there is a solution region?"""
        cell = self._create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()
        cell.metadata['nbgrader'] = dict(solution=True)

        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert_equal(cell.source, "something something\nYOUR ANSWER HERE")
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_text_cell_region(self):
        """Is a text grade cell correctly cleared when there is a solution region?"""
        cell = self._create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()

        cell = self.preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert_equal(cell.source, "something something\nYOUR ANSWER HERE")
        assert cell.metadata.nbgrader['solution']

    def _test_preprocess_notebook(self, name):
        """Is the test notebook processed without error?"""
        try:
            self.preprocessor.preprocess(self.nbs[name], {})
        except Exception:
            print(traceback.print_exc())
            raise AssertionError("{} failed to process".format(name))

    def test_preprocess_nb(self):
        for name in self.files:
            yield self._test_preprocess_notebook, name

    def _test_remove_celltoolbar(self, name):
        """Is the celltoolbar removed?"""
        nb = self.nbs[name]
        nb.metadata['celltoolbar'] = 'Create Assignment'
        nb = self.preprocessor.preprocess(nb, {})[0]
        assert 'celltoolbar' not in nb.metadata, name

    def test_remove_celltoolbar(self):
        for name in self.files:
            yield self._test_remove_celltoolbar, name
