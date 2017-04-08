import os
import json

from tornado import web

from .base import BaseApiHandler
from ...api import MissingEntry


def orthogonal_score_data(value, max_value):
    value = value or 0
    max_value = max_value or 0
    return dict(
        display = "{:.2f} / {:.2f}".format(value, max_value),
        sort = value if max_value == 0 else value / max_value,
    )


def orthogonal_tick_data(tick, string):
    html = '<span class="glyphicon glyphicon-ok"></span>'
    return dict(
        display = html if tick else "",
        search = string if tick else "",
        sort = 0 if tick else 1,
    )


class GradeCollectionHandler(BaseApiHandler):
    @web.authenticated
    def get(self):
        submission_id = self.get_argument("submission_id")
        try:
            notebook = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps([g.to_dict() for g in notebook.grades]))


class CommentCollectionHandler(BaseApiHandler):
    @web.authenticated
    def get(self):
        submission_id = self.get_argument("submission_id")
        try:
            notebook = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps([c.to_dict() for c in notebook.comments]))


class GradeHandler(BaseApiHandler):
    @web.authenticated
    def get(self, grade_id):
        try:
            grade = self.gradebook.find_grade_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps(grade.to_dict()))

    @web.authenticated
    def put(self, grade_id):
        try:
            grade = self.gradebook.find_grade_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)

        data = self.get_json_body()
        grade.manual_score = data.get("manual_score", None)
        if grade.manual_score is None and grade.auto_score is None:
            grade.needs_manual_grade = True
        else:
            grade.needs_manual_grade = False
        self.gradebook.db.commit()
        self.write(json.dumps(grade.to_dict()))


class CommentHandler(BaseApiHandler):
    @web.authenticated
    def get(self, grade_id):
        try:
            comment = self.gradebook.find_comment_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps(comment.to_dict()))

    @web.authenticated
    def put(self, grade_id):
        try:
            comment = self.gradebook.find_comment_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)

        data = self.get_json_body()
        comment.manual_comment = data.get("manual_comment", None)
        self.gradebook.db.commit()
        self.write(json.dumps(comment.to_dict()))


class FlagSubmissionHandler(BaseApiHandler):
    @web.authenticated
    def post(self, submission_id):
        try:
            submission = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)

        submission.flagged = not submission.flagged
        self.gradebook.db.commit()
        self.write(json.dumps(submission.to_dict()))


class AssignmentsDataTableHandler(BaseApiHandler):

    def _orthogonal_data(self, assignment):
        ave = self.gradebook.average_assignment_score(assignment.name)
        assignment = assignment.to_dict()
        assignment["average_score"] = ave
        for key, value in assignment.items():
            if "score" in key:
                assignment[key] = "{:.2f}".format(value)
        return assignment

    @web.authenticated
    def get(self):
        assignments = []
        for assignment in self.gradebook.assignments:
            assignments.append(self._orthogonal_data(assignment))
        self.write(json.dumps(dict(data=assignments)))


class AssignmentNotebooksDataTableHandler(BaseApiHandler):

    def _orthogonal_data(self, notebook, assignment):
        args = (notebook.name, assignment.name)
        notebook = notebook.to_dict()
        notebook["ave_score"] = orthogonal_score_data(
            self.gradebook.average_notebook_score(*args),
            notebook.pop("max_score"),
        )
        notebook["ave_code_score"] = orthogonal_score_data(
            self.gradebook.average_notebook_code_score(*args),
            notebook.pop("max_code_score"),
        )
        notebook["ave_written_score"] = orthogonal_score_data(
            self.gradebook.average_notebook_written_score(*args),
            notebook.pop("max_written_score"),
        )
        notebook["needs_manual_grade"] = orthogonal_tick_data(
            notebook["needs_manual_grade"], "needs_manual_grade")
        return notebook

    @web.authenticated
    def get(self, assignment_id):
        try:
            assignment = self.gradebook.find_assignment(assignment_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid assignment: {}".format(assignment_id))

        notebooks = []
        for notebook in assignment.notebooks:
            notebooks.append(self._orthogonal_data(notebook, assignment))
        self.write(json.dumps(dict(data=notebooks)))


class AssignmentNotebookSubmissionsDataTableHandler(BaseApiHandler):

    def _filter_existing_notebooks(self, assignment_id, notebook_id, notebooks):
        submissions = list()
        notebook_dir_format = os.path.join(self.notebook_dir_format, "{notebook_id}.ipynb")
        for nb_dict in notebooks:
            filename = os.path.join(
                self.notebook_dir,
                notebook_dir_format.format(
                    nbgrader_step=self.nbgrader_step,
                    assignment_id=assignment_id,
                    notebook_id=notebook_id,
                    student_id=nb_dict['student']
                )
            )
            if os.path.exists(filename):
                submissions.append(nb_dict)
        return submissions

    def _orthogonal_data(self, submission, index):
        submission['index'] = index
        submission["score"] = orthogonal_score_data(
            submission["score"], submission.pop("max_score"))
        submission["code_score"] = orthogonal_score_data(
            submission["code_score"], submission.pop("max_code_score"))
        submission["written_score"] = orthogonal_score_data(
            submission["written_score"], submission.pop("max_written_score"))
        submission["needs_manual_grade"] = orthogonal_tick_data(
            submission["needs_manual_grade"], "needs_manual_grade")
        submission["failed_tests"] = orthogonal_tick_data(
            submission["failed_tests"], "tests failed")
        submission["flagged"] = orthogonal_tick_data(
            submission["flagged"], "flagged")
        return submission

    @web.authenticated
    def get(self, assignment_id, notebook_id):
        try:
            self.gradebook.find_notebook(notebook_id, assignment_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid notebook: {}/{}".format(assignment_id, notebook_id))

        notebook_dicts = self.gradebook.notebook_submission_dicts(notebook_id, assignment_id)
        submissions = sorted(
            self._filter_existing_notebooks(assignment_id, notebook_id, notebook_dicts),
            key=lambda x: ['id']
        )
        for i, submission in enumerate(submissions):
            submissions[i] = self._orthogonal_data(submission, i+1)
        self.write(json.dumps(dict(data=submissions)))


class StudentsDataTablesHandler(BaseApiHandler):

    def _orthogonal_data(self, student):
        student["last_name"] = student["last_name"] or "Unkown"
        student["first_name"] = student["first_name"] or "Unkown"
        student["score"] = orthogonal_score_data(
            student["score"], student.pop("max_score"))
        return student

    @web.authenticated
    def get(self):
        students = []
        for student in self.gradebook.student_dicts():
            students.append(self._orthogonal_data(student))
        self.write(json.dumps(dict(data=students)))


class StudentAssignmentsDataTablesHandler(BaseApiHandler):

    def _orthogonal_data(self, assignment, student):
        try:
            submission = self.gradebook.find_submission(
                assignment.name, student.id
            ).to_dict()
        except MissingEntry:
            submission = dict()

        data = assignment.to_dict()
        data['id'] = submission.get('id', None)
        data['score'] = orthogonal_score_data(
            submission.get('score', 0), data.pop('max_score'))
        data['code_score'] = orthogonal_score_data(
            submission.get('code_score', 0), data.pop('max_code_score'))
        data['written_score'] = orthogonal_score_data(
            submission.get('written_score', 0), data.pop('max_written_score'))
        data["needs_manual_grade"] = orthogonal_tick_data(
            submission.get("needs_manual_grade", False), "needs_manual_grade")
        return data


    @web.authenticated
    def get(self, student_id):
        try:
            student = self.gradebook.find_student(student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid student: {}".format(student_id))

        assignments = []
        for assignment in self.gradebook.assignments:
            assignments.append(self._orthogonal_data(assignment, student))
        self.write(json.dumps(dict(data=assignments)))


class StudentAssignmentNotebooksDataTableHandler(BaseApiHandler):

    def _filter_existing_notebooks(self, assignment, assignment_id, student_id):
        submissions = list()
        notebook_dir_format = os.path.join(self.notebook_dir_format, "{notebook_id}.ipynb")
        for notebook in assignment.notebooks:
            filename = os.path.join(
                self.notebook_dir,
                notebook_dir_format.format(
                    nbgrader_step=self.nbgrader_step,
                    assignment_id=assignment_id,
                    notebook_id=notebook.name,
                    student_id=student_id
                )
            )
            if os.path.exists(filename):
                submissions.append(notebook.to_dict())
        return submissions

    def _orthogonal_data(self, submission):
        submission["score"] = orthogonal_score_data(
            submission["score"], submission.pop("max_score"))
        submission["code_score"] = orthogonal_score_data(
            submission["code_score"], submission.pop("max_code_score"))
        submission["written_score"] = orthogonal_score_data(
            submission["written_score"], submission.pop("max_written_score"))
        submission["needs_manual_grade"] = orthogonal_tick_data(
            submission["needs_manual_grade"], "needs_manual_grade")
        submission["failed_tests"] = orthogonal_tick_data(
            submission["failed_tests"], "tests failed")
        submission["flagged"] = orthogonal_tick_data(
            submission["flagged"], "flagged")
        return submission

    @web.authenticated
    def get(self, student_id, assignment_id):
        try:
            assignment = self.gradebook.find_submission(assignment_id, student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid assignment: {} for {}".format(assignment_id, student_id))

        submissions = self._filter_existing_notebooks(assignment, assignment_id, student_id)
        for i, submission in enumerate(submissions):
            submissions[i] = self._orthogonal_data(submission)
        self.write(json.dumps(dict(data=submissions)))


default_handlers = [
    (r"/formgrader/api/grades", GradeCollectionHandler),
    (r"/formgrader/api/comments", CommentCollectionHandler),
    (r"/formgrader/api/grade/([^/]+)", GradeHandler),
    (r"/formgrader/api/comment/([^/]+)", CommentHandler),
    (r"/formgrader/api/submission/([^/]+)/flag", FlagSubmissionHandler),

    (r"/formgrader/api/assignments", AssignmentsDataTableHandler),
    (r"/formgrader/api/assignments/([^/]+)", AssignmentNotebooksDataTableHandler),
    (r"/formgrader/api/assignments/([^/]+)/([^/]+)", AssignmentNotebookSubmissionsDataTableHandler),

    (r"/formgrader/api/students", StudentsDataTablesHandler),
    (r"/formgrader/api/students/([^/]+)", StudentAssignmentsDataTablesHandler),
    (r"/formgrader/api/students/([^/]+)/([^/]+)", StudentAssignmentNotebooksDataTableHandler),
]
