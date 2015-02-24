from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode
from nbgrader import utils
from nbgrader.api import Gradebook

class SaveGradeCells(Preprocessor):
    """A preprocessor to save information about grade cells."""

    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to database")
    assignment_id = Unicode(u'assignment', config=True, help="Assignment ID")

    def preprocess(self, nb, resources):
        self.gradebook = Gradebook(self.db_url)

        self.notebook_id = resources['unique_key']
        self.gradebook.update_or_create_notebook(
            self.notebook_id, self.assignment_id)

        self.comment_index = 0

        nb, resources = super(SaveGradeCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            max_score = float(cell.metadata.nbgrader['points'])            

            # we only want the source and checksum for non-solution cells
            if utils.is_solution(cell):
                source = None
                checksum = None
                cell_type = None
            else:
                source = cell.source
                checksum = cell.metadata.nbgrader['checksum']
                cell_type = cell.cell_type

            grade_cell = self.gradebook.update_or_create_grade_cell(
                cell.metadata.nbgrader.grade_id,
                self.notebook_id,
                self.assignment_id,
                max_score=max_score,
                source=source,
                checksum=checksum,
                cell_type=cell_type)

            self.log.debug("Recorded grade cell %s into database", grade_cell)

        if utils.is_solution(cell):
            solution_cell = self.gradebook.update_or_create_solution_cell(
                self.comment_index,
                self.notebook_id,
                self.assignment_id)

            self.comment_index += 1
            self.log.debug("Recorded solution cell %s into database", solution_cell)

        return cell, resources
