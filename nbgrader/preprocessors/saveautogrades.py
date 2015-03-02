from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from nbgrader import utils
from nbgrader.api import Gradebook


class SaveAutoGrades(Preprocessor):
    """Preprocessor for saving out the autograder grades into a database"""

    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to database")

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']

        # connect to the mongo database
        self.gradebook = Gradebook(self.db_url)
        self.gradebook.update_or_create_submission(
            self.assignment_id, self.student_id)

        # process the cells
        nb, resources = super(SaveAutoGrades, self).preprocess(nb, resources)

        return nb, resources

    def _add_score(self, cell, resources):
        """Graders can override the autograder grades, and may need to
        manually grade written solutions anyway. This function adds
        score information to the database if it doesn't exist. It does
        NOT override the 'score' field, as this is the manual score
        that might have been provided by a grader.

        """
        # these are the fields by which we will identify the score
        # information
        grade = self.gradebook.find_grade(
            cell.metadata['nbgrader']['grade_id'],
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        # determine what the grade is
        auto_score, max_score = utils.determine_grade(cell)
        assert max_score == grade.max_score
        grade.auto_score = auto_score
        self.gradebook.db.commit()
        self.log.debug(grade)

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._add_score(cell, resources)

        return cell, resources
