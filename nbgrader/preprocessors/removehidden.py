
import re

from .. import utils
from . import NbGraderPreprocessor

class RemoveHidden(NbGraderPreprocessor):

    def preprocess_cell(self, cell, resources, cell_index):

        if utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell):
            cell.source = re.sub('START(?:.|\n)*?STOP', '', cell.source)

            # we probably don't really need this? 
            cell.metadata.nbgrader['oldchecksum'] = cell.metadata.nbgrader['checksum']
            cell.metadata.nbgrader['checksum'] = utils.compute_checksum(cell)


        return cell, resources
