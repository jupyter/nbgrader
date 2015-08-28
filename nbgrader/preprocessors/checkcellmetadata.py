import re

from .. import utils
from . import NbGraderPreprocessor

class CheckCellMetadata(NbGraderPreprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb, resources):
        resources['grade_ids'] = ids = []
        nb, resources = super(CheckCellMetadata, self).preprocess(nb, resources)

        id_set = set([])
        for grade_id in ids:
            if grade_id in id_set:
                raise RuntimeError("Duplicate grade id: {}".format(grade_id))
            id_set.add(grade_id)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell) or utils.is_solution(cell):
            # check for invalid grade ids
            grade_id = cell.metadata.nbgrader.get("grade_id", "")
            if not re.match(r"^[a-zA-Z0-9_\-]+$", grade_id):
                raise RuntimeError("Invalid grade id: {}".format(grade_id))
            resources['grade_ids'].append(grade_id)

        if utils.is_grade(cell):
            # check for valid points
            points = cell.metadata.nbgrader.get("points", "")
            try:
                points = float(points)
            except ValueError:
                raise RuntimeError(
                    "Point value for grade cell {} is invalid: {}".format(
                        grade_id, points))

        # check that markdown cells are grade AND solution (not either/or)
        if cell.cell_type == "markdown" and utils.is_grade(cell) and not utils.is_solution(cell):
            raise RuntimeError(
                "Markdown grade cell '{}' is not marked as a solution cell".format(
                    grade_id))
        if cell.cell_type == "markdown" and not utils.is_grade(cell) and utils.is_solution(cell):
            raise RuntimeError(
                "Markdown solution cell (index {}) is not marked as a grade cell".format(
                    cell_index))

        if 'nbgrader' in cell.metadata and 'grade_id' in cell.metadata.nbgrader:
            if (not utils.is_grade(cell) and not utils.is_solution(cell) and not utils.is_locked(cell)):
                self.log.warn("Removing unused grade_id from cell {}".format(cell_index))
                del cell.metadata.nbgrader['grade_id']

        return cell, resources
