import sys

from IPython.utils.traitlets import Bool

from nbgrader import utils
from nbgrader.api import Gradebook
from nbgrader.preprocessors import NbGraderPreprocessor

from textwrap import dedent

class SaveCells(NbGraderPreprocessor):
    """A preprocessor to save information about grade and solution cells."""

    create_assignment = Bool(
        False, config=True,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        )
    )

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.db_url = resources['nbgrader']['db_url']

        if self.notebook_id == '':
            self.log.error("Invalid notebook id: '%s'", self.notebook_id)
            sys.exit(1)
        if self.assignment_id == '':
            self.log.error("Invalid assignment id: '%s'", self.assignment_id)
            sys.exit(1)

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        # create the assignment, if so directed
        if self.create_assignment:
            self.gradebook.update_or_create_assignment(self.assignment_id)

        # create the notebook
        self.gradebook.update_or_create_notebook(
            self.notebook_id, self.assignment_id)

        self.comment_index = 0

        nb, resources = super(SaveCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            max_score = float(cell.metadata.nbgrader['points'])
            cell_type = cell.cell_type
            source = cell.source
            checksum = cell.metadata.nbgrader.get('checksum', None)

            grade_cell = self.gradebook.update_or_create_grade_cell(
                cell.metadata.nbgrader['grade_id'],
                self.notebook_id,
                self.assignment_id,
                max_score=max_score,
                source=source,
                checksum=checksum,
                cell_type=cell_type)

            self.log.debug("Recorded grade cell %s into database", grade_cell)

        if utils.is_solution(cell):
            cell_type = cell.cell_type
            source = cell.source
            checksum = cell.metadata.nbgrader.get('checksum', None)

            solution_cell = self.gradebook.update_or_create_solution_cell(
                self.comment_index,
                self.notebook_id,
                self.assignment_id,
                cell_type=cell_type,
                source=source,
                checksum=checksum)

            self.comment_index += 1
            self.log.debug("Recorded solution cell %s into database", solution_cell)

        return cell, resources
