from traitlets import Bool

from .. import utils
from . import NbGraderPreprocessor

class LockCells(NbGraderPreprocessor):
    """A preprocessor for making cells undeletable."""

    lock_solution_cells = Bool(True, config=True, help="Whether solution cells are undeletable")
    lock_grade_cells = Bool(True, config=True, help="Whether grade cells are undeletable")
    lock_readonly_cells = Bool(True, config=True, help="Whether readonly cells are undeletable")
    lock_all_cells = Bool(False, config=True, help="Whether all assignment cells are undeletable")

    def preprocess_cell(self, cell, resources, cell_index):
        if self.lock_all_cells:
            cell.metadata['deletable'] = False
        elif self.lock_grade_cells and utils.is_grade(cell):
            cell.metadata['deletable'] = False
        elif self.lock_solution_cells and utils.is_solution(cell):
            cell.metadata['deletable'] = False
        elif self.lock_readonly_cells and utils.is_locked(cell):
            cell.metadata['deletable'] = False
        return cell, resources
