from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode
from nbgrader import utils
from nbgrader.api import Gradebook

class OverwriteGradeCells(Preprocessor):
    """A preprocessor to save information about grade cells."""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        nb, resources = super(OverwriteGradeCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            grade_cell = self.gradebook.find_grade_cell(
                cell.metadata.nbgrader.grade_id,
                self.notebook_id,
                self.assignment_id)

            cell.metadata.nbgrader['points'] = grade_cell.max_score

            # we only want the source and checksum for non-solution cells
            if not utils.is_solution(cell) and grade_cell.source:
                old_checksum = grade_cell.checksum
                new_checksum = utils.compute_checksum(cell)

                if old_checksum != new_checksum:
                    self.log.warning("Checksum for grade cell %s has changed!", grade_cell.name)

                cell.source = grade_cell.source
                cell.cell_type = grade_cell.cell_type
                cell.metadata.nbgrader['checksum'] = grade_cell.checksum

            self.log.debug("Overwrote grade cell %s", grade_cell.name)

        return cell, resources
