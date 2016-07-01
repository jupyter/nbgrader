
import re

from .. import utils
from . import NbGraderPreprocessor
from traitlets import Unicode
from textwrap import dedent

class RemoveHidden(NbGraderPreprocessor):
    hidestart = Unicode(
        '### HIDESTART',
        config=True,
        help=dedent(
            """
            Suppose you want to hide some test cases from your students in a cell.
            Place this string before those test cases and the corresponding string
            hideend after them.
            """
        )
    )

    hideend = Unicode(
        '### HIDEEND',
        config=True,
        help=dedent(
            """
            Suppose you want to hide some test cases from your students in a cell.
            Place this string after those tests.
            """
        )
    )

    def preprocess_cell(self, cell, resources, cell_index):

        if utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell):
            cell.source = re.sub('{}(?:.|\n)*?{}'.format(self.hidestart,
                                                         self.hideend)
                                 , '', cell.source)

            # we probably don't really need this? 
            cell.metadata.nbgrader['oldchecksum'] = cell.metadata.nbgrader['checksum']
            cell.metadata.nbgrader['checksum'] = utils.compute_checksum(cell)


        return cell, resources
