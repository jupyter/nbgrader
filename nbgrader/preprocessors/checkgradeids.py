from IPython.nbconvert.preprocessors import Preprocessor
from nbgrader import utils

class CheckGradeIds(Preprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb, resources):
        resources['grade_ids'] = ids = []
        nb, resources = super(CheckGradeIds, self).preprocess(nb, resources)

        id_set = set([])
        for grade_id in ids:
            if grade_id in id_set:
                raise RuntimeError("Duplicate grade id: {}".format(grade_id))
            id_set.add(grade_id)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            grade_id = cell.metadata.nbgrader.get("grade_id", "")
            if grade_id == "":
                raise RuntimeError("Blank grade id!")
            resources['grade_ids'].append(grade_id)

            points = cell.metadata.nbgrader.get("points", "")
            try:
                points = float(points)
            except ValueError:
                raise RuntimeError(
                    "Point value for grade cell {} is invalid: {}".format(
                        grade_id, points))

        return cell, resources
