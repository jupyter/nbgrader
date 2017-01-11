import os
import re

from tornado import web

from .base import BaseHandler
from ..api import MissingEntry


class AssignmentsHandler(BaseHandler):
    @web.authenticated
    def get(self):
        assignments = []
        for assignment in self.gradebook.assignments:
            x = assignment.to_dict()
            x["average_score"] = self.gradebook.average_assignment_score(assignment.name)
            x["average_code_score"] = self.gradebook.average_assignment_code_score(assignment.name)
            x["average_written_score"] = self.gradebook.average_assignment_written_score(assignment.name)
            assignments.append(x)

        html = self.render(
            "assignments.tpl",
            assignments=assignments,
            base_url=self.auth.base_url)

        self.write(html)


class AssignmentNotebooksHandler(BaseHandler):
    @web.authenticated
    def get(self, assignment_id):
        try:
            assignment = self.gradebook.find_assignment(assignment_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid assignment: {}".format(assignment_id))

        notebooks = []
        for notebook in assignment.notebooks:
            x = notebook.to_dict()
            x["average_score"] = self.gradebook.average_notebook_score(notebook.name, assignment.name)
            x["average_code_score"] = self.gradebook.average_notebook_code_score(notebook.name, assignment.name)
            x["average_written_score"] = self.gradebook.average_notebook_written_score(notebook.name, assignment.name)
            notebooks.append(x)
        assignment = assignment.to_dict()

        html = self.render(
            "assignment_notebooks.tpl",
            assignment=assignment,
            notebooks=notebooks,
            base_url=self.auth.base_url)

        self.write(html)


class AssignmentNotebookSubmissionsHandler(BaseHandler):
    @web.authenticated
    def get(self, assignment_id, notebook_id):
        try:
            self.gradebook.find_notebook(notebook_id, assignment_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid notebook: {}/{}".format(assignment_id, notebook_id))

        notebook_dir_format = os.path.join(self.notebook_dir_format, "{notebook_id}.ipynb")
        notebook_dicts = self.gradebook.notebook_submission_dicts(notebook_id, assignment_id)

        submissions = list()
        for nb_dict in notebook_dicts:
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

        submissions.sort(key=lambda x: x["id"])
        for i, submission in enumerate(submissions):
            submission["index"] = i

        html = self.render(
            "notebook_submissions.tpl",
            notebook_id=notebook_id,
            assignment_id=assignment_id,
            submissions=submissions,
            base_url=self.auth.base_url)

        self.write(html)


class StudentsHandler(BaseHandler):
    @web.authenticated
    def get(self):
        students = self.gradebook.student_dicts()
        students.sort(key=lambda x: x.get("last_name") or "no last name")

        html = self.render(
            "students.tpl",
            students=students,
            base_url=self.auth.base_url)

        self.write(html)


class StudentAssignmentsHandler(BaseHandler):
    @web.authenticated
    def get(self, student_id):
        try:
            student = self.gradebook.find_student(student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid student: {}".format(student_id))

        submissions = []
        for assignment in self.gradebook.assignments:
            try:
                submission = self.gradebook.find_submission(assignment.name, student.id).to_dict()
            except MissingEntry:
                submission = {
                    "id": None,
                    "name": assignment.name,
                    "student": student.id,
                    "duedate": None,
                    "timestamp": None,
                    "extension": None,
                    "total_seconds_late": 0,
                    "score": 0,
                    "max_score": assignment.max_score,
                    "code_score": 0,
                    "max_code_score": assignment.max_code_score,
                    "written_score": 0,
                    "max_written_score": assignment.max_written_score,
                    "needs_manual_grade": False
                }
            submissions.append(submission)

        submissions.sort(key=lambda x: x.get("duedate") or "no due date")
        student = student.to_dict()

        html = self.render(
            "student_assignments.tpl",
            assignments=submissions,
            student=student,
            base_url=self.auth.base_url)

        self.write(html)


class StudentAssignmentNotebooksHandler(BaseHandler):
    @web.authenticated
    def get(self, student_id, assignment_id):
        try:
            assignment = self.gradebook.find_submission(assignment_id, student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid assignment: {} for {}".format(assignment_id, student_id))


        notebook_dir_format = os.path.join(self.notebook_dir_format, "{notebook_id}.ipynb")

        submissions = list()
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

        submissions.sort(key=lambda x: x['name'])

        html = self.render(
            "student_submissions.tpl",
            assignment_id=assignment_id,
            student=assignment.student.to_dict(),
            submissions=submissions,
            base_url=self.auth.base_url)

        self.write(html)


class SubmissionHandler(BaseHandler):
    @web.authenticated
    def get(self, submission_id):
        try:
            submission = self.gradebook.find_submission_notebook_by_id(submission_id)
            assignment_id = submission.assignment.assignment.name
            notebook_id = submission.notebook.name
            student_id = submission.student.id
        except MissingEntry:
            raise web.HTTPError(404, "Invalid submission: {}".format(submission_id))

        # redirect if there isn't a trailing slash in the uri
        if os.path.split(self.request.path)[1] == submission_id:
            url = self.request.path + '/'
            if self.request.query:
                url += '?' + self.request.query
            return self.redirect(url, permanent=True)

        notebook_dir_format = os.path.join(self.notebook_dir_format, "{notebook_id}.ipynb")
        filename = os.path.join(self.notebook_dir, notebook_dir_format.format(
            nbgrader_step=self.nbgrader_step,
            assignment_id=assignment_id,
            notebook_id=notebook_id,
            student_id=student_id))

        submissions = self.gradebook.notebook_submissions(notebook_id, assignment_id)
        submission_ids = sorted([x.id for x in submissions])
        ix = submission_ids.index(submission.id)
        server_exists = self.auth.notebook_server_exists()
        server_cookie = self.auth.get_notebook_server_cookie()

        if self.mathjax_url.startswith("http"):
            mathjax_url = self.mathsjax_url
        else:
            mathjax_url = self.auth.base_url + '/mathjax/MathJax.js'

        resources = {
            'assignment_id': assignment_id,
            'notebook_id': notebook_id,
            'submission_id': submission.id,
            'index': ix,
            'total': len(submissions),
            'notebook_server_exists': server_exists,
            'base_url': self.auth.base_url,
            'mathjax_url': mathjax_url,
            'last_name': submission.student.last_name,
            'first_name': submission.student.first_name
        }

        if server_exists:
            relative_path = os.path.relpath(filename, self.notebook_dir)
            resources['notebook_path'] = self.auth.get_notebook_url(relative_path)

        if not os.path.exists(filename):
            resources['filename'] = filename
            html = self.render('formgrade_404.tpl', resources=resources)
            self.clear()
            self.set_status(404)
            self.write(html)
        else:
            html, _ = self.exporter.from_filename(filename, resources=resources)
            if server_cookie:
                self.set_cookie(**server_cookie)
            self.write(html)


class SubmissionNavigationHandler(BaseHandler):

    def _assignment_notebook_list_url(self, assignment_id, notebook_id):
        return '{}/assignments/{}/{}'.format(self.auth.base_url, assignment_id, notebook_id)

    def _submission_url(self, submission_id):
        url = '{}/submissions/{}'.format(self.auth.base_url, submission_id)
        if self.get_argument('index', default=None) is not None:
            return "{}?index={}".format(url, self.get_argument('index'))
        else:
            return url

    def _get_submission_ids(self, assignment_id, notebook_id):
        submissions = self.gradebook.notebook_submissions(notebook_id, assignment_id)
        return sorted([x.id for x in submissions])

    def _get_incorrect_submission_ids(self, assignment_id, notebook_id, submission):
        submissions = self.gradebook.notebook_submissions(notebook_id, assignment_id)
        incorrect_ids = set([x.id for x in submissions if x.failed_tests])
        incorrect_ids.add(submission.id)
        incorrect_ids = sorted(incorrect_ids)
        return incorrect_ids

    def _next(self, assignment_id, notebook_id, submission):
        # find next submission
        submission_ids = self._get_submission_ids(assignment_id, notebook_id)
        ix = submission_ids.index(submission.id)
        if ix == (len(submission_ids) - 1):
            return self._assignment_notebook_list_url(assignment_id, notebook_id)
        else:
            return self._submission_url(submission_ids[ix + 1])

    def _prev(self, assignment_id, notebook_id, submission):
        # find previous submission
        submission_ids = self._get_submission_ids(assignment_id, notebook_id)
        ix = submission_ids.index(submission.id)
        if ix == 0:
            return self._assignment_notebook_list_url(assignment_id, notebook_id)
        else:
            return self._submission_url(submission_ids[ix - 1])

    def _next_incorrect(self, assignment_id, notebook_id, submission):
        # find next incorrect submission
        submission_ids = self._get_incorrect_submission_ids(assignment_id, notebook_id, submission)
        ix_incorrect = submission_ids.index(submission.id)
        if ix_incorrect == (len(submission_ids) - 1):
            return self._assignment_notebook_list_url(assignment_id, notebook_id)
        else:
            return self._submission_url(submission_ids[ix_incorrect + 1])

    def _prev_incorrect(self, assignment_id, notebook_id, submission):
        # find previous incorrect submission
        submission_ids = self._get_incorrect_submission_ids(assignment_id, notebook_id, submission)
        ix_incorrect = submission_ids.index(submission.id)
        if ix_incorrect == 0:
            return self._assignment_notebook_list_url(assignment_id, notebook_id)
        else:
            return self._submission_url(submission_ids[ix_incorrect - 1])

    @web.authenticated
    def get(self, submission_id, action):
        try:
            submission = self.gradebook.find_submission_notebook_by_id(submission_id)
            assignment_id = submission.assignment.assignment.name
            notebook_id = submission.notebook.name
        except MissingEntry:
            raise web.HTTPError(404, "Invalid submission: {}".format(submission_id))

        handler = getattr(self, '_{}'.format(action))
        self.redirect(handler(assignment_id, notebook_id, submission), permanent=False)


class SubmissionFilesHandler(web.StaticFileHandler, BaseHandler):
    def initialize(self, default_filename=None):
        super(SubmissionFilesHandler, self).initialize(
            self.notebook_dir, default_filename=default_filename)

    def parse_url_path(self, url_path):
        submission_id, path = re.match(r"([^/]+)/(.*)", url_path.lstrip("/")).groups()

        try:
            submission = self.gradebook.find_submission_notebook_by_id(submission_id)
            assignment_id = submission.assignment.assignment.name
            student_id = submission.student.id
        except MissingEntry:
            raise web.HTTPError(404, "Invalid submission: {}".format(submission_id))

        dirname = os.path.join(self.notebook_dir, self.notebook_dir_format.format(
            nbgrader_step=self.nbgrader_step,
            assignment_id=assignment_id,
            student_id=student_id))

        full_path = os.path.join(dirname, path)
        return super(SubmissionFilesHandler, self).parse_url_path(full_path)

    @web.authenticated
    def get(self, *args, **kwargs):
        return super(SubmissionFilesHandler, self).get(*args, **kwargs)


class Template404(BaseHandler):
    """Render our 404 template"""
    def prepare(self):
        raise web.HTTPError(404)


root_path = os.path.dirname(__file__)
template_path = os.path.join(root_path, 'templates')
static_path = os.path.join(root_path, 'static')
components_path = os.path.join(static_path, 'components')
fonts_path = os.path.join(components_path, 'bootstrap', 'fonts')

_navigation_regex = r"(?P<action>next_incorrect|prev_incorrect|next|prev)"

default_handlers = [
    (r"/", AssignmentsHandler),
    (r"/assignments/?", AssignmentsHandler),
    (r"/assignments/([^/]+)/?", AssignmentNotebooksHandler),
    (r"/assignments/([^/]+)/([^/]+)/?", AssignmentNotebookSubmissionsHandler),

    (r"/students/?", StudentsHandler),
    (r"/students/([^/]+)/?", StudentAssignmentsHandler),
    (r"/students/([^/]+)/([^/]+)/?", StudentAssignmentNotebooksHandler),

    (r"/submissions/components/(.*)", web.StaticFileHandler, {'path': components_path}),
    (r"/submissions/([^/]+)/?", SubmissionHandler),
    (r"/submissions/(?P<submission_id>[^/]+)/%s/?" % _navigation_regex, SubmissionNavigationHandler),
    (r"/submissions/(.*)", SubmissionFilesHandler),

    (r"/fonts/(.*)", web.StaticFileHandler, {'path': fonts_path})
]
