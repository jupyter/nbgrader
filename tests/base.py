from IPython.nbformat.current import read as read_nb
from IPython.nbformat.current import new_code_cell, new_text_cell


class TestBase(object):

    def setup(self):
        with open("tests/files/test.ipynb", "r") as fh:
            self.nb = read_nb(fh, 'ipynb')
        self.cells = self.nb.worksheets[0].cells

    @staticmethod
    def _create_code_cell():
        source = """# YOUR CODE HERE
{% if solution %}
print("hello")
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
