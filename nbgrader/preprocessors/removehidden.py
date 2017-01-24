
import re

from .. import utils
from . import NbGraderPreprocessor

class RemoveHidden(NbGraderPreprocessor):

    def preprocess_cell(self, cell, resources, cell_index):

        cell.source = re.sub('START(?:.|\n)*?STOP', '', cell.source)

        return cell, resources
