from traitlets import Integer

from .. import utils
from . import NbGraderPreprocessor

class LimitTestCellHeights(NbGraderPreprocessor):
    """A preprocessor for making test cells not be too large."""

    test_cell_height = Integer(
        100,
        help="Max height of a test cell"
    ).tag(config=True)


    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            cell.metadata['max_height'] = self.test_cell_height
        return cell, resources
