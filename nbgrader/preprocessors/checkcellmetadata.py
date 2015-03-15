from IPython.nbconvert.preprocessors import Preprocessor
from nbgrader import utils

class CheckCellMetadata(Preprocessor):
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
        if utils.is_grade(cell):
            # check for blank grade ids
            grade_id = cell.metadata.nbgrader.get("grade_id", "")
            if grade_id == "":
                raise RuntimeError("Blank grade id!")
            resources['grade_ids'].append(grade_id)

            # check for valid points
            points = cell.metadata.nbgrader.get("points", "")
            try:
                points = float(points)
            except ValueError:
                raise RuntimeError(
                    "Point value for grade cell {} is invalid: {}".format(
                        grade_id, points))

        # check that code cells are grade OR solution (not both)
        if cell.cell_type == "code" and utils.is_grade(cell) and utils.is_solution(cell):
            raise RuntimeError(
                "Code grade cell '{}' is also marked as a solution cell".format(
                    grade_id))

        # check that markdown cells are grade AND solution (not either/or)
        if cell.cell_type == "markdown" and utils.is_grade(cell) and not utils.is_solution(cell):
            raise RuntimeError(
                "Markdown grade cell '{}' is not marked as a solution cell".format(
                    grade_id))
        if cell.cell_type == "markdown" and not utils.is_grade(cell) and utils.is_solution(cell):
            raise RuntimeError(
                "Markdown solution cell (index {}) is not marked as a grade cell".format(
                    cell_index))

        return cell, resources
