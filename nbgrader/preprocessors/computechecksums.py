from IPython.nbconvert.preprocessors import Preprocessor
from .. import utils

class ComputeChecksums(Preprocessor):
    """A preprocessor to compute checksums of grade cells."""

    def preprocess(self, nb, resources):
        self.comment_index = 0
        nb, resources = super(ComputeChecksums, self).preprocess(nb, resources)
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # compute checksums of grade cell and solution cells
        if utils.is_grade(cell) or utils.is_solution(cell):
            checksum = utils.compute_checksum(cell)
            cell.metadata.nbgrader['checksum'] = checksum

            if utils.is_grade(cell):
                self.log.debug(
                    "Checksum for '%s' is %s",
                    cell.metadata.nbgrader['grade_id'],
                    checksum)
            if utils.is_solution(cell):
                self.log.debug(
                    "Checksum for solution cell #%s is %s",
                    self.comment_index,
                    checksum)
                self.comment_index += 1

        return cell, resources
