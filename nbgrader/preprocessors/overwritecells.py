from IPython.nbformat.v4.nbbase import validate

from nbgrader import utils
from nbgrader.api import Gradebook
from nbgrader.preprocessors import NbGraderPreprocessor

class OverwriteCells(NbGraderPreprocessor):
    """A preprocessor to overwrite information about grade and solution cells."""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        nb, resources = super(OverwriteCells, self).preprocess(nb, resources)

        return nb, resources

    def update_cell_type(self, cell, cell_type):
        if cell.cell_type == cell_type:
            return
        elif cell_type == 'code':
            cell.cell_type = 'code'
            cell.outputs = []
            cell.execution_count = None
            validate(cell, 'code_cell')
        elif cell_type == 'markdown':
            cell.cell_type = 'markdown'
            if 'outputs' in cell:
                del cell['outputs']
            if 'execution_count' in cell:
                del cell['execution_count']
            validate(cell, 'markdown_cell')

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            grade_cell = self.gradebook.find_grade_cell(
                cell.metadata.nbgrader["grade_id"],
                self.notebook_id,
                self.assignment_id)

            cell.metadata.nbgrader['points'] = grade_cell.max_score

            # we only want the source and checksum for non-solution cells
            if not utils.is_solution(cell):
                old_checksum = grade_cell.checksum
                new_checksum = utils.compute_checksum(cell)

                if old_checksum != new_checksum:
                    self.log.warning("Checksum for grade cell %s has changed!", grade_cell.name)

                cell.source = grade_cell.source
                cell.metadata.nbgrader['checksum'] = grade_cell.checksum
                self.update_cell_type(cell, grade_cell.cell_type)

            self.log.debug("Overwrote grade cell %s", grade_cell.name)

        if utils.is_solution(cell):
            solution_cell = self.gradebook.find_solution_cell(
                cell.metadata.nbgrader["grade_id"],
                self.notebook_id,
                self.assignment_id)

            old_checksum = solution_cell.checksum
            new_checksum = utils.compute_checksum(cell)

            if cell.cell_type != solution_cell.cell_type:
                self.log.warning("Cell type for solution cell %s has changed!", solution_cell.name)

            cell.metadata.nbgrader['checksum'] = solution_cell.checksum
            self.update_cell_type(cell, solution_cell.cell_type)

            self.log.debug("Overwrote solution cell #%s", solution_cell.name)

        return cell, resources
