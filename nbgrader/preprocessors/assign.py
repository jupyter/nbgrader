from IPython.nbconvert.preprocessors import ExecutePreprocessor
from IPython.utils.traitlets import Bool


class Assign(ExecutePreprocessor):

    solution = Bool(False, config=True, help="Whether to generate the release version, or the solutions")

    def _preprocess_nb(self, nb, resources):

        # remove the cell toolbar, if it exists
        if "celltoolbar" in nb.metadata:
            del nb.metadata['celltoolbar']

        return nb, resources

    def preprocess(self, nb, resources):
        nb, resources = self._preprocess_nb(nb, resources)

        if self.solution:
            nb, resources = super(Assign, self).preprocess(
                nb, resources)
        else:
            nb, resources = super(ExecutePreprocessor, self).preprocess(
                nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):

        # if it's the solution version, execute the cell
        if cell.cell_type == 'code' and self.solution:
            cell, resources = super(Assign, self)\
                .preprocess_cell(cell, resources, cell_index)

        return cell, resources
