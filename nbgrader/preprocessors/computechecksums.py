from IPython.nbconvert.preprocessors import Preprocessor
from .. import utils

class ComputeChecksums(Preprocessor):
    """A preprocessor to compute checksums of grade cells."""

    def preprocess_cell(self, cell, resources, cell_index):
        # compute checksums of grade cells, but not those of solution
        # cells, because solution cells will be modified by students
        if utils.is_grade(cell) and not utils.is_solution(cell):
            checksum = utils.compute_checksum(cell)
            cell.metadata.nbgrader['checksum'] = checksum
            self.log.debug(
                "Checksum for '%s' is %s",
                cell.metadata.nbgrader['grade_id'],
                checksum)

        return cell, resources
