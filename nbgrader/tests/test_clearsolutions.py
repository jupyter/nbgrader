from nose.tools import assert_raises
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
        assert pp.begin_solution == "%!!foo"
        assert pp.end_solution == "%@@bar"

    def test_replace_solution_region_code(self):
        """Are solution regions in code cells correctly replaced?"""
        cell = self._create_code_cell()
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert cell.input == """print("something")\n# YOUR CODE HERE\nraise NotImplementedError()"""

    def test_replace_solution_region_text(self):
        """Are solution regions in text cells correctly replaced?"""
        cell = self._create_text_cell()
        cell.source = "something something\n### BEGIN SOLUTION\nthis is the answer!\n### END SOLUTION"
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert cell.source == "something something\nYOUR ANSWER HERE"

    def test_dont_replace_solution_region(self):
        """Is false returned when there is no solution region?"""
        cell = self._create_text_cell()
        replaced_solution = self.preprocessor._replace_solution_region(cell)
        assert not replaced_solution

    def test_replace_solution_region_no_end(self):
        """Is an error thrown when there is no end solution statement?"""
        cell = self._create_text_cell()
        cell.source = "something something\n### BEGIN SOLUTION\nthis is the answer!"
        assert_raises(RuntimeError, self.preprocessor._replace_solution_region, cell)

    def test_replace_solution_region_nested_solution(self):
        """Is an error thrown when there are nested solution statements?"""
        cell = self._create_text_cell()
        cell.source = "something something\n### BEGIN SOLUTION\n### BEGIN SOLUTION\nthis is the answer!\n### END SOLUTION"
        assert_raises(RuntimeError, self.preprocessor._replace_solution_region, cell)

    def test_preprocess_code_cell_student(self):
        """Is the student version of a code cell correctly preprocessed?"""
        cell = self._create_code_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """print("something")\n# YOUR CODE HERE\nraise NotImplementedError()"""

    def test_preprocess_code_cell_solution(self):
        """Is a code solution cell correctly cleared when there is a solution region?"""
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = dict(solution=True)

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """print("something")\n# YOUR CODE HERE\nraise NotImplementedError()"""

    def test_preprocess_code_cell_solution_no_region(self):
        """Is a code solution cell correctly cleared when there is no solution region?"""
        cell = self._create_code_cell()
        cell.input = """print("the answer!")"""
        cell.metadata['nbgrader'] = dict(solution=True)

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """# YOUR CODE HERE\nraise NotImplementedError()"""

    def test_preprocess_text_cell_solution(self):
        """Is a text grade cell correctly cleared when there is a solution region?"""
        cell = self._create_text_cell()
        cell.metadata['nbgrader'] = dict(solution=True)

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.source == """YOUR ANSWER HERE"""

    def test_preprocess_text_cell_solution_no_region(self):
        """Is a text grade cell correctly cleared when there is no solution region?"""
        cell = self._create_text_cell()
        cell.source = "something something\n### BEGIN SOLUTION\nthis is the answer!\n### END SOLUTION"
        cell.metadata['nbgrader'] = dict(solution=True)

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.source == """something something\nYOUR ANSWER HERE"""

    def test_preprocess_nb(self):
        """Is the test notebook processed without error?"""
        self.preprocessor.preprocess(self.nb, {})
