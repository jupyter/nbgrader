import os
import re

from tornado import web

from .base import BaseHandler
from ...api import MissingEntry


class AssignmentsHandler(BaseHandler):
    @web.authenticated
    def get(self):
        html = self.render("assignments.tpl")
        self.write(html)


class AssignmentNotebooksHandler(BaseHandler):
    @web.authenticated
    def get(self, assignment_id):
        html = self.render(
            "assignment_notebooks.tpl",
            assignment_id=assignment_id,
            base_url=self.base_url,
        )
        self.write(html)


class AssignmentNotebookSubmissionsHandler(BaseHandler):
    @web.authenticated
    def get(self, assignment_id, notebook_id):
        html = self.render(
            "notebook_submissions.tpl",
            notebook_id=notebook_id,
            assignment_id=assignment_id,
            base_url=self.base_url
        )
        self.write(html)


class StudentsHandler(BaseHandler):
    @web.authenticated
    def get(self):
        html = self.render("students.tpl", base_url=self.base_url)
        self.write(html)


class StudentAssignmentsHandler(BaseHandler):
    @web.authenticated
    def get(self, student_id):
        try:
            student = self.gradebook.find_student(student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid student: {}".format(student_id))

        html = self.render(
            "student_assignments.tpl",
            student=student.to_dict(),
            base_url=self.base_url
        )
        self.write(html)


class StudentAssignmentNotebooksHandler(BaseHandler):
    @web.authenticated
    def get(self, student_id, assignment_id):
        try:
            student = self.gradebook.find_student(student_id)
        except MissingEntry:
            raise web.HTTPError(404, "Invalid student: {}".format(student_id))

        html = self.render(
            "student_submissions.tpl",
            assignment_id=assignment_id,
            student=student.to_dict(),
            base_url=self.base_url
        )
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

        relative_path = os.path.relpath(filename, self.notebook_dir)
        resources = {
            'assignment_id': assignment_id,
            'notebook_id': notebook_id,
            'submission_id': submission.id,
            'index': ix,
            'total': len(submissions),
            'base_url': self.base_url,
            'mathjax_url': self.mathjax_url,
            'last_name': submission.student.last_name,
            'first_name': submission.student.first_name,
            'notebook_path': self.notebook_url_prefix + '/' + relative_path
        }

        if not os.path.exists(filename):
            resources['filename'] = filename
            html = self.render('formgrade_404.tpl', resources=resources)
            self.clear()
            self.set_status(404)
            self.write(html)
        else:
            html, _ = self.exporter.from_filename(filename, resources=resources)
            self.write(html)


class SubmissionNavigationHandler(BaseHandler):

    def _assignment_notebook_list_url(self, assignment_id, notebook_id):
        return '{}/formgrader/assignments/{}/{}'.format(self.base_url, assignment_id, notebook_id)

    def _submission_url(self, submission_id):
        url = '{}/formgrader/submissions/{}'.format(self.base_url, submission_id)
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
    (r"/formgrader/?", AssignmentsHandler),
    (r"/formgrader/assignments/?", AssignmentsHandler),
    (r"/formgrader/assignments/([^/]+)/?", AssignmentNotebooksHandler),
    (r"/formgrader/assignments/([^/]+)/([^/]+)/?", AssignmentNotebookSubmissionsHandler),

    (r"/formgrader/students/?", StudentsHandler),
    (r"/formgrader/students/([^/]+)/?", StudentAssignmentsHandler),
    (r"/formgrader/students/([^/]+)/([^/]+)/?", StudentAssignmentNotebooksHandler),

    (r"/formgrader/submissions/components/(.*)", web.StaticFileHandler, {'path': components_path}),
    (r"/formgrader/submissions/([^/]+)/?", SubmissionHandler),
    (r"/formgrader/submissions/(?P<submission_id>[^/]+)/%s/?" % _navigation_regex, SubmissionNavigationHandler),
    (r"/formgrader/submissions/(.*)", SubmissionFilesHandler),

    (r"/formgrader/fonts/(.*)", web.StaticFileHandler, {'path': fonts_path})
]
