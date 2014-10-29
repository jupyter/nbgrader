from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from pymongo import MongoClient
from nbgrader import utils


class SaveAutoGrades(Preprocessor):
    """Preprocessor for saving out the autograder grades into a MongoDB"""

    ip = Unicode("localhost", config=True, help="IP address for the database")
    port = Integer(27017, config=True, help="Port for the database")

    def preprocess(self, nb, resources):
        # connect to the mongo database
        client = MongoClient(self.ip, self.port)
        db = client['assignments']
        self.grades = db['grades']
        self.comments = db['comments']

        # keep track of the number of comments we add
        self.comment_index = 0

        # process the cells
        nb, resources = super(SaveAutoGrades, self).preprocess(nb, resources)

        return nb, resources

    def _add_comment(self, cell, resources):
        """Graders can optionally add comments to the student's solutions, so
        add the comment information into the database if it doesn't
        already exist. It should NOT overwrite existing comments that
        might have been added by a grader already.

        """

        # these are the fields that we use to identify the specific
        # comment in the database
        comment_id = {
            "notebook": resources['unique_key'],
            "student_id": resources['nbgrader']['student_id'],
            "comment_id": self.comment_index
        }

        # try to look up the comment -- if it doesn't exist, create it
        comment = self.comments.find_one(comment_id)
        if comment is None:
            comment = {"comment": ""}
            comment.update(comment_id)
            self.comments.insert(comment)

        # update the number of comments we have inserted
        self.comment_index += 1

    def _add_score(self, cell, resources):
        """Graders can override the autograder grades, and may need to
        manually grade written solutions anyway. This function adds
        score information to the database if it doesn't exist. It does
        NOT override the 'score' field, as this is the manual score
        that might have been provided by a grader.

        """
        # these are the fields by which we will identify the score
        # information
        grade_id = {
            "notebook": resources['unique_key'],
            "student_id": resources['nbgrader']['student_id'],
            "grade_id": cell.metadata['nbgrader']['grade_id']
        }

        # try to look up the grade -- if it doesn't exist, create it
        grade = self.grades.find_one(grade_id)
        if grade is None:
            grade = grade_id.copy()
            self.grades.insert(grade)

        # set the maximum earnable score
        points = float(cell.metadata['nbgrader']['points'])
        grade['max_score'] = points

        # If it's a code cell and it threw an error, then they get
        # zero points, otherwise they get max_score points. If it's a
        # text cell, we can't autograde it.
        if cell.cell_type == 'code':
            autoscore = points
            for output in cell.outputs:
                if output.output_type == 'pyerr':
                    autoscore = 0
                    break
            grade['autoscore'] = float(autoscore)

        else:
            grade['autoscore'] = None

        # Update the grade information and print it out
        self.grades.update(grade_id, {"$set": grade})
        print(grade)

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a solution cell, then add a comment
        if utils.is_solution(cell):
            self._add_comment(cell, resources)

        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._add_score(cell, resources)

        return cell, resources
