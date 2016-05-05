from .. import utils
from ..api import Gradebook
from ..plugins import LateSubmissionPlugin
from . import NbGraderPreprocessor


class AssignLatePenalties(NbGraderPreprocessor, LateSubmissionPlugin):
    """Preprocessor for assigning penalties for late submissions to the database"""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        try:
            # process the late submissions
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

            if late_penalty is not None:
                assignment.late_submission_penalty = late_penalty
                self.gradebook.db.commit()

        finally:
            self.gradebook.db.close()

        return nb, resources
