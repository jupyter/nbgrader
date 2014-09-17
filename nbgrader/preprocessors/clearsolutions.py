from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode
from nbgrader import utils


class ClearSolutions(Preprocessor):

    code_stub = Unicode("# YOUR CODE HERE\nraise NotImplementedError()", config=True)
    markdown_stub = Unicode("YOUR ANSWER HERE", config=True)

    def __init__(self, *args, **kwargs):
        super(ClearSolutions, self).__init__(*args, **kwargs)

    def preprocess_cell(self, cell, resources, cell_index):
        cell_type = utils.get_assignment_cell_type(cell)

        # replace code solution cells with the code stub
        if cell.cell_type == 'code' and cell_type == 'solution':
            cell.input = self.code_stub

        # replace markdown grade cells with the markdown stub
        elif cell.cell_type == 'markdown' and cell_type == 'grade':
            cell.source = self.markdown_stub

        # replace solution areas in code cells with the code stub
        elif cell.cell_type == 'code':
            lines = cell.input.split('\n')
            new_lines = []
            in_solution = False

            for line in lines:
                # begin the solution area
                if line.strip() == "### BEGIN SOLUTION":
                    in_solution = True
                    # replace it with the code stub, indented as necessary
                    indent = line[:line.find('#')]
                    for stub_line in self.code_stub.split("\n"):
                        new_lines.append(indent + stub_line)

                # end the solution area
                elif line.strip() == "### END SOLUTION":
                    in_solution = False

                # add lines as long as it's not in the solution area
                elif not in_solution:
                    new_lines.append(line)

            # replace the cell input
            cell.input = '\n'.join(new_lines)

        return cell, resources
