from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from nbgrader import utils
from nbgrader.api import Gradebook

class SaveGradeCells(Preprocessor):
    """A preprocessor to save information about grade cells."""

    db_name = Unicode("gradebook", config=True, help="Database name")
    db_ip = Unicode("localhost", config=True, help="IP address for the database")
    db_port = Integer(27017, config=True, help="Port for the database")

    assignment_id = Unicode(u'assignment', config=True, help="Assignment ID")

    def preprocess(self, nb, resources):
        # connect to the mongo database
        self.gradebook = Gradebook(self.db_name, ip=self.db_ip, port=self.db_port)
        self.assignment = self.gradebook.find_assignment(
            assignment_id=self.assignment_id)
        self.notebook_id = resources['unique_key']

        nb, resources = super(SaveGradeCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            grade_cell = self.gradebook.find_or_create_grade_cell(
                grade_id=cell.metadata.nbgrader.grade_id,
                notebook_id=self.notebook_id,
                assignment=self.assignment)

            grade_cell.max_score = float(cell.metadata.nbgrader['points'])

            # we only want the source and checksum for non-solution cells
            if utils.is_solution(cell):
                grade_cell.source = None
                grade_cell.checksum = None
                grade_cell.cell_type = None
            else:
                grade_cell.source = cell.source
                grade_cell.checksum = cell.metadata.nbgrader['checksum']
                grade_cell.cell_type = cell.cell_type

            self.gradebook.update_grade_cell(grade_cell)
            self.log.debug("Recorded grade cell %s into database", grade_cell.grade_id)

        return cell, resources
