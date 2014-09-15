from IPython.nbformat.current import read as read_nb
from IPython.nbformat.current import new_code_cell, new_text_cell
from nbgrader.preprocessors import RenderSolutions
from nbgrader import utils


class TestRenderSolutions(object):

    def setup(self):
        with open("tests/files/test.ipynb", "r") as fh:
            self.nb = read_nb(fh, 'ipynb')
        self.preprocessor = RenderSolutions()

    @staticmethod
    def _create_code_cell():
        source = """# YOUR CODE HERE
{% if solution %}
print "hello"
{% endif %}
"""
        cell = new_code_cell(input=source, prompt_number=2, outputs=["foo"])
        return cell

    @staticmethod
    def _create_text_cell():
        source = """{% if solution %}
this is the answer!
{% else %}
YOUR ANSWER HERE
{% endif %}
"""
        cell = new_text_cell('markdown', source=source)
        return cell

    def test_filter_solution(self):
        """Are release and skip cells filtered out when solution=True?"""
        self.preprocessor.solution = True
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        for cell in nb.worksheets[0].cells:
            cell_type = utils.get_assignment_cell_type(cell)
            assert cell_type != 'skip'
            assert cell_type != 'release'

    def test_filter_release(self):
        """Are solution and skip cells filtered out when solution=False?"""
        self.preprocessor.solution = False
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        for cell in nb.worksheets[0].cells:
            cell_type = utils.get_assignment_cell_type(cell)
            assert cell_type != 'skip'
            assert cell_type != 'solution'

    def test_preprocess_code_cell_solution(self):
        """Is the solution version of a code cell correctly preprocessed?"""
        self.preprocessor.solution = True
        self.preprocessor.toc = ""
        cell = self._create_code_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)

        assert cell.input == """# YOUR CODE HERE\nprint "hello\""""

    def test_preprocess_code_cell_release(self):
        """Is the release version of a code cell correctly preprocessed?"""
        self.preprocessor.solution = False
        self.preprocessor.toc = ""
        cell = self._create_code_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.input == """# YOUR CODE HERE"""

    def test_preprocess_text_cell_solution(self):
        """Is the solution version of a text cell correctly preprocessed?"""
        self.preprocessor.solution = True
        self.preprocessor.toc = ""
        cell = self._create_text_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.source == """this is the answer!"""

    def test_preprocess_text_cell_release(self):
        """Is the release version of a text cell correctly preprocessed?"""
        self.preprocessor.solution = False
        self.preprocessor.toc = ""
        cell = self._create_text_cell()

        cell, resources = self.preprocessor.preprocess_cell(cell, {}, 1)
        assert cell.source == """YOUR ANSWER HERE"""
