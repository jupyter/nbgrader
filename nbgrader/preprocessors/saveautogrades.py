from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from nbgrader import utils
from nbgrader.api import Gradebook


class SaveAutoGrades(Preprocessor):
    """Preprocessor for saving out the autograder grades into a MongoDB"""

    ip = Unicode("localhost", config=True, help="IP address for the database")
    port = Integer(27017, config=True, help="Port for the database")

    def preprocess(self, nb, resources):
        # connect to the mongo database
        self.gradebook = Gradebook()
        self.student = self.gradebook.find_student(
            student_id=resources['nbgrader']['student_id'])
        self.notebook = self.gradebook.find_or_create_notebook(
            notebook_id=resources['unique_key'],
            student=self.student)

        # keep track of the number of comments we add
        self.comment_index = 0

        # process the cells
        nb, resources = super(SaveAutoGrades, self).preprocess(nb, resources)

        # save the notebook id
        if 'nbgrader' not in nb.metadata:
            nb.metadata['nbgrader'] = {}
        nb.metadata['nbgrader']['notebook_id'] = self.notebook.notebook_id
        nb.metadata['nbgrader']['notebook_uuid'] = self.notebook._id

        return nb, resources

    def _add_comment(self, cell, resources):
        """Graders can optionally add comments to the student's solutions, so
        add the comment information into the database if it doesn't
        already exist. It should NOT overwrite existing comments that
        might have been added by a grader already.

        """

        # retrieve or create the comment object from the database
        comment = self.gradebook.find_or_create_comment(
            notebook=self.notebook,
            comment_id=self.comment_index)

        # update the number of comments we have inserted
        self.comment_index += 1
        self.log.debug(comment)

    def _add_score(self, cell, resources):
        """Graders can override the autograder grades, and may need to
        manually grade written solutions anyway. This function adds
        score information to the database if it doesn't exist. It does
        NOT override the 'score' field, as this is the manual score
        that might have been provided by a grader.

        """
        # these are the fields by which we will identify the score
        # information
        grade = self.gradebook.find_or_create_grade(
            notebook=self.notebook,
            grade_id=cell.metadata['nbgrader']['grade_id'])

        # set the maximum earnable score
        points = float(cell.metadata['nbgrader']['points'])
        grade.max_score = points

        # If it's a code cell and it threw an error, then they get
        # zero points, otherwise they get max_score points. If it's a
        # text cell, we can't autograde it.
        if cell.cell_type == 'code':
            grade.autoscore = points
            for output in cell.outputs:
                if output.output_type == 'pyerr':
                    grade.autoscore = 0
                    break

        else:
            grade.autoscore = None

        # Update the grade information and print it out
        self.gradebook.update_grade(grade)
        self.log.debug(grade)

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a solution cell, then add a comment
        if utils.is_solution(cell):
            self._add_comment(cell, resources)

        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._add_score(cell, resources)

        return cell, resources
