from IPython.nbconvert.preprocessors import Preprocessor
from nbgrader import utils


class DisplayAutoGrades(Preprocessor):
    """Preprocessor for displaying the autograder grades"""

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a grade cell, the add a grade
        if not utils.is_grade(cell):
            print("not a grade cell")
            return cell, resources

        score, max_score = utils.determine_grade(cell)

        # it's a markdown cell, so we can't do anything
        # TODO: make sure they at least wrote something?
        if score is None:
            print("markdown cell")
            return cell, resources

        if score < max_score:
            print("-" * 80)
            print("VALIDATION FAILED!")
            print(cell.source)

        return cell, resources
