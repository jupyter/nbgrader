from IPython.nbconvert.preprocessors import *
from IPython.utils.traitlets import Unicode
from nbgrader.utils import is_solution

class ClearSolutions(Preprocessor):
    """A preprocessor for configuraing embedded Google Forms for grading."""
    
    solution_stub = Unicode(u'Use this cell for your solution', config=True)

    def preprocess_cell(self, cell, resources, cell_index):
        if is_solution(cell):
            if cell.cell_type == 'code':
                cell.input = '#' + self.solution_stub
            else:
                cell.input = self.solution_stub
        return cell, resources
