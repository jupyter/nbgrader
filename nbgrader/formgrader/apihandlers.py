import json

from tornado import web

from .base import BaseApiHandler
from ..api import MissingEntry


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


default_handlers = [
    (r"/api/grades", GradeCollectionHandler),
    (r"/api/comments", CommentCollectionHandler),
    (r"/api/grade/([^/]+)", GradeHandler),
    (r"/api/comment/([^/]+)", CommentHandler),
    (r"/api/submission/([^/]+)/flag", FlagSubmissionHandler)
]
