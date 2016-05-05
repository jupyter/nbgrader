from .. import utils
from ..api import Gradebook
from ..plugins import LateSubmissionPlugin
from . import NbGraderPreprocessor


class GetGrades(NbGraderPreprocessor, LateSubmissionPlugin):
    """Preprocessor for saving grades from the database to the notebook"""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        try:
            # process the cells
            nb, resources = super(GetGrades, self).preprocess(nb, resources)
            assignment = self.gradebook.find_submission(
                self.assignment_id, self.student_id)
            notebook = self.gradebook.find_submission_notebook(
                self.notebook_id, self.assignment_id, self.student_id)

            late_penalty = None
            if assignment.total_seconds_late > 0:
                self.log.warning("{} is {} seconds late".format(
                    assignment, assignment.total_seconds_late))
                late_penalty = self.late_submission_penalty(assignment, notebook)
                self.log.warning("Late submission penalty: {}".format(late_penalty))

            resources['nbgrader']['score'] = notebook.score
            resources['nbgrader']['max_score'] = notebook.max_score
            if late_penalty is not None:
                assignment.late_submission_penalty = late_penalty
                resources['nbgrader']['score'] -= late_penalty
                resources['nbgrader']['late_penalty'] = late_penalty
                self.gradebook.db.commit()

        finally:
            self.gradebook.db.close()

        return nb, resources

    def _get_comment(self, cell, resources):
        """Graders can optionally add comments to the student's solutions, so
        add the comment information into the database if it doesn't
        already exist. It should NOT overwrite existing comments that
        might have been added by a grader already.

        """

        # retrieve or create the comment object from the database
        comment = self.gradebook.find_comment(
            cell.metadata['nbgrader']['grade_id'],
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        # save it in the notebook
        cell.metadata.nbgrader['comment'] = comment.comment

    def _get_score(self, cell, resources):
        grade = self.gradebook.find_grade(
            cell.metadata['nbgrader']['grade_id'],
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        cell.metadata.nbgrader['score'] = grade.score
        cell.metadata.nbgrader['points'] = grade.max_score

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a solution cell, then add a comment
        if utils.is_solution(cell):
            self._get_comment(cell, resources)

        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._get_score(cell, resources)

        return cell, resources
