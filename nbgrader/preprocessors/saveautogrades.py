from nbgrader import utils
from nbgrader.api import Gradebook
from nbgrader.preprocessors import NbGraderPreprocessor


class SaveAutoGrades(NbGraderPreprocessor):
    """Preprocessor for saving out the autograder grades into a database"""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']
        self.db_url = resources['nbgrader']['db_url']

        # get the timestamp
        timestamp = resources['nbgrader'].get('timestamp', None)
        if timestamp:
            kwargs = {'timestamp': timestamp}
        else:
            kwargs = {}

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        submission = self.gradebook.update_or_create_submission(
            self.assignment_id, self.student_id, **kwargs)

        # if the submission is late, print out how many seconds late it is
        self.log.info("%s submitted at %s", submission, timestamp)
        if timestamp and submission.total_seconds_late > 0:
            self.log.warning("%s is %s seconds late", submission, submission.total_seconds_late)

        self.comment_index = 0

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
        grade.auto_score = auto_score
        self.gradebook.db.commit()
        self.log.debug(grade)

    def _add_comment(self, cell, resources):
        comment = self.gradebook.find_comment(
            self.comment_index,
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        if comment.comment:
            return
        elif cell.metadata.nbgrader.get("checksum", None) == utils.compute_checksum(cell):
            comment.comment = "No response."
            self.gradebook.db.commit()
            self.log.debug(comment)

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._add_score(cell, resources)

        if utils.is_solution(cell):
            self._add_comment(cell, resources)
            self.comment_index += 1

        return cell, resources
