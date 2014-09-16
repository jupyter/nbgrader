from nbgrader.preprocessors import ClearSolutions

from .base import TestBase


class TestClearSolutions(TestBase):

    def setup(self):
        super(TestClearSolutions, self).setup()
        self.preprocessor = ClearSolutions()

    def test_preprocess_code_cell_student(self):
        """Is the student version of a code cell correctly preprocessed?"""
        cell = self._create_code_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """print("something")\n# YOUR CODE HERE\nraise NotImplementedError"""

    def test_preprocess_code_cell_solution(self):
        """Is a code solution cell correctly cleared?"""
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = dict(cell_type='solution')

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """# YOUR CODE HERE\nraise NotImplementedError"""

    def test_preprocess_text_cell_solution(self):
        """Is a markdown grade cell correctly cleared?"""
        cell = self._create_text_cell()
        cell.metadata['nbgrader'] = dict(cell_type='grade')

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.source == """YOUR ANSWER HERE"""
