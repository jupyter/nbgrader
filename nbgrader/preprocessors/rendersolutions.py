from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Bool, Unicode
from nbgrader import utils


class RenderSolutions(Preprocessor):

    solution = Bool(False, config=True, help="Whether to generate the release version, or the solutions")
    title = Unicode("", config=True, help="Title of the assignment")

    def __init__(self, *args, **kwargs):
        super(RenderSolutions, self).__init__(*args, **kwargs)
        self.env = utils.make_jinja_environment()

    def preprocess(self, nb, resources):
        """Filter out cells, depending on the value of `self.solution`:

        * always filter out 'skip' cells
        * if self.solution == True, then filter out 'release' cells
        * if self.release == True, then filter out 'solution' cells

        """
        for worksheet in nb.worksheets:
            new_cells = []

            for cell in worksheet.cells:
                # get the cell type
                cell_type = utils.get_assignment_cell_type(cell)

                # determine whether the cell should be included
                if cell_type == 'skip':
                    continue
                elif cell_type == 'release' and self.solution:
                    continue
                elif cell_type == 'solution' and not self.solution:
                    continue
                else:
                    cell, resources = self.preprocess_cell(
                        cell, resources, len(new_cells))
                    new_cells.append(cell)

            worksheet.cells = new_cells

        # remove the toolbar setting
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        kwargs = {
            "solution": self.solution,
            "title": self.title,
            "toc": resources.get('toc', '')
        }

        # render templates in code cells
        if cell.cell_type == 'code':
            template = self.env.from_string(cell.input)
            rendered = template.render(solution=self.solution)
            if rendered[-1] == "\n":
                rendered = rendered[:-1]
            cell.input = rendered

        # render templates in markdown/heading cells
        elif cell.cell_type in ('markdown', 'heading'):
            template = self.env.from_string(cell.source)
            rendered = template.render(**kwargs)
            if rendered[-1] == "\n":
                rendered = rendered[:-1]
            cell.source = rendered

        return cell, resources
