import json
import os
from functools import wraps
from nbgrader.api import MissingEntry
from flask import Flask, request, abort, redirect, url_for, render_template, \
    send_from_directory, Blueprint, g

app = Flask(__name__, static_url_path='')
blueprint = Blueprint('formgrade', __name__)

def auth(f):
    """Authenticated flask app route."""

    @wraps(f)
    def authenticated(*args, **kwargs):
        result = app.auth.authenticate()
        if result is True:
            pass  # Success
        elif result is False:
            abort(403)  # Forbidden
        else:
            return result  # Redirect
        return f(*args, **kwargs)

    return authenticated


@blueprint.url_defaults
def bp_url_defaults(endpoint, values):
    name = getattr(g, 'name', None)
    if name is not None:
        values.setdefault('name', name)


@blueprint.url_value_preprocessor
def bp_url_value_preprocessor(endpoint, values):
    g.name = values.pop('name')


@blueprint.route("/static/<path:filename>")
@auth
def static_proxy(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


@blueprint.route("/fonts/<filename>")
@auth
def fonts(filename):
    return redirect(url_for('.static', filename=os.path.join("fonts", filename)))


@blueprint.route("/")
@auth
def home():
    return redirect(url_for('.view_assignments'))


@blueprint.route("/assignments/")
@auth
def view_assignments():
    assignments = []
    for assignment in app.gradebook.assignments:
        x = assignment.to_dict()
        x["average_score"] = app.gradebook.average_assignment_score(assignment.name)
        x["average_code_score"] = app.gradebook.average_assignment_code_score(assignment.name)
        x["average_written_score"] = app.gradebook.average_assignment_written_score(assignment.name)
        assignments.append(x)
    return render_template(
        "assignments.tpl",
        assignments=assignments,
        base_url=app.auth.base_url)


@blueprint.route("/students/")
@auth
def view_students():
    students = app.gradebook.student_dicts()
    students.sort(key=lambda x: x.get("last_name") or "no last name")
    return render_template(
        "students.tpl",
        students=students,
        base_url=app.auth.base_url)


@blueprint.route("/assignments/<assignment_id>/")
@auth
def view_assignment(assignment_id):
    try:
        assignment = app.gradebook.find_assignment(assignment_id)
    except MissingEntry:
        abort(404)

    notebooks = []
    for notebook in assignment.notebooks:
        x = notebook.to_dict()
        x["average_score"] = app.gradebook.average_notebook_score(notebook.name, assignment.name)
        x["average_code_score"] = app.gradebook.average_notebook_code_score(notebook.name, assignment.name)
        x["average_written_score"] = app.gradebook.average_notebook_written_score(notebook.name, assignment.name)
        notebooks.append(x)
    assignment = assignment.to_dict()

    return render_template(
        "assignment_notebooks.tpl",
        assignment=assignment,
        notebooks=notebooks,
        base_url=app.auth.base_url)


@blueprint.route("/students/<student_id>/")
@auth
def view_student(student_id):
    try:
        student = app.gradebook.find_student(student_id)
    except MissingEntry:
        abort(404)

    assignments = [x.to_dict() for x in student.submissions]
    assignments.sort(key=lambda x: x.get("duedate") or "no due date")
    student = student.to_dict()

    return render_template(
        "student_assignments.tpl",
        assignments=assignments,
        student=student,
        base_url=app.auth.base_url)


@blueprint.route("/assignments/<assignment_id>/<notebook_id>/")
@auth
def view_assignment_notebook(assignment_id, notebook_id):
    try:
        app.gradebook.find_notebook(notebook_id, assignment_id)
    except MissingEntry:
        abort(404)

    submissions = app.gradebook.notebook_submission_dicts(notebook_id, assignment_id)
    submissions.sort(key=lambda x: x["id"])

    for i, submission in enumerate(submissions):
        submission["index"] = i

    return render_template(
        "notebook_submissions.tpl",
        notebook_id=notebook_id,
        assignment_id=assignment_id,
        submissions=submissions,
        base_url=app.auth.base_url)


@blueprint.route("/students/<student_id>/<assignment_id>/")
@auth
def view_student_assignment(student_id, assignment_id):
    try:
        assignment = app.gradebook.find_submission(assignment_id, student_id)
    except MissingEntry:
        abort(404)

    submissions = [n.to_dict() for n in assignment.notebooks]
    submissions.sort(key=lambda x: x['name'])

    return render_template(
        "student_submissions.tpl",
        assignment_id=assignment_id,
        student=assignment.student.to_dict(),
        submissions=submissions,
        base_url=app.auth.base_url
    )


@blueprint.route("/submissions/<submission_id>/<path:path>")
@auth
def view_submission_files(submission_id, path):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        student_id = submission.student.id
    except MissingEntry:
        abort(404)

    dirname = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        nbgrader_step=app.nbgrader_step,
        assignment_id=assignment_id,
        student_id=student_id))

    return send_from_directory(dirname, path)


@blueprint.route("/submissions/<submission_id>/next")
@auth
def view_next_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
    except MissingEntry:
        abort(404)

    submissions = app.gradebook.notebook_submissions(notebook_id, assignment_id)

    # find next submission
    submission_ids = sorted([x.id for x in submissions])
    ix = submission_ids.index(submission.id)
    if ix == (len(submissions) - 1):
        return redirect(url_for('.view_assignment_notebook', assignment_id=assignment_id, notebook_id=notebook_id))
    else:
        return redirect(url_for('.view_submission', submission_id=submission_ids[ix + 1]))


@blueprint.route("/submissions/<submission_id>/next_incorrect")
@auth
def view_next_incorrect_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
    except MissingEntry:
        abort(404)

    submissions = app.gradebook.notebook_submission_dicts(notebook_id, assignment_id)

    # find next incorrect submission
    incorrect_ids = set([x['id'] for x in submissions if x['failed_tests']])
    incorrect_ids.add(submission.id)
    incorrect_ids = sorted(incorrect_ids)
    ix_incorrect = incorrect_ids.index(submission.id)
    if ix_incorrect == (len(incorrect_ids) - 1):
        return redirect(url_for('.view_assignment_notebook', assignment_id=assignment_id, notebook_id=notebook_id))
    else:
        return redirect(url_for('.view_submission', submission_id=incorrect_ids[ix_incorrect + 1]))


@blueprint.route("/submissions/<submission_id>/prev")
@auth
def view_prev_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
    except MissingEntry:
        abort(404)

    submissions = app.gradebook.notebook_submissions(notebook_id, assignment_id)

    # find previous submission
    submission_ids = sorted([x.id for x in submissions])
    ix = submission_ids.index(submission.id)
    if ix == 0:
        return redirect(url_for('.view_assignment_notebook', assignment_id=assignment_id, notebook_id=notebook_id))
    else:
        return redirect(url_for('.view_submission', submission_id=submission_ids[ix - 1]))


@blueprint.route("/submissions/<submission_id>/prev_incorrect")
@auth
def view_prev_incorrect_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
    except MissingEntry:
        abort(404)

    submissions = app.gradebook.notebook_submission_dicts(notebook_id, assignment_id)

    # find previous incorrect submission
    incorrect_ids = set([x['id'] for x in submissions if x['failed_tests']])
    incorrect_ids.add(submission.id)
    incorrect_ids = sorted(incorrect_ids)
    ix_incorrect = incorrect_ids.index(submission.id)
    if ix_incorrect == 0:
        return redirect(url_for('.view_assignment_notebook', assignment_id=assignment_id, notebook_id=notebook_id))
    else:
        return redirect(url_for('.view_submission', submission_id=incorrect_ids[ix_incorrect - 1]))


@blueprint.route("/submissions/<submission_id>/")
@auth
def view_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
        student_id = submission.student.id
    except MissingEntry:
        abort(404)

    notebook_dir_format = os.path.join(app.notebook_dir_format, "{notebook_id}.ipynb")
    filename = os.path.join(app.notebook_dir, notebook_dir_format.format(
        nbgrader_step=app.nbgrader_step,
        assignment_id=assignment_id,
        notebook_id=notebook_id,
        student_id=student_id))

    if not os.path.exists(filename):
        abort(404)

    submissions = app.gradebook.notebook_submissions(notebook_id, assignment_id)
    submission_ids = sorted([x.id for x in submissions])
    ix = submission_ids.index(submission.id)
    server_exists = app.auth.notebook_server_exists()
    resources = {
        'assignment_id': assignment_id,
        'notebook_id': notebook_id,
        'submission_id': submission.id,
        'index': ix,
        'total': len(submissions),
        'notebook_server_exists': server_exists,
        'base_url': app.auth.base_url
    }

    if server_exists:
        relative_path = os.path.relpath(filename, app.notebook_dir)
        resources['notebook_path'] = app.auth.get_notebook_url(relative_path)

    output, resources = app.exporter.from_filename(filename, resources=resources)
    return output


@blueprint.route("/api/grades")
@auth
def get_all_grades():
    submission_id = request.args["submission_id"]

    try:
        notebook = app.gradebook.find_submission_notebook_by_id(submission_id)
    except MissingEntry:
        abort(404)

    return json.dumps([g.to_dict() for g in notebook.grades])


@blueprint.route("/api/comments")
@auth
def get_all_comments():
    submission_id = request.args["submission_id"]

    try:
        notebook = app.gradebook.find_submission_notebook_by_id(submission_id)
    except MissingEntry:
        abort(404)

    return json.dumps([c.to_dict() for c in notebook.comments])


@blueprint.route("/api/grade/<_id>", methods=["GET", "PUT"])
@auth
def get_grade(_id):
    try:
        grade = app.gradebook.find_grade_by_id(_id)
    except MissingEntry:
        abort(404)

    if request.method == "PUT":
        grade.manual_score = request.json.get("manual_score", None)
        app.gradebook.db.commit()

    return json.dumps(grade.to_dict())


@blueprint.route("/api/comment/<_id>", methods=["GET", "PUT"])
@auth
def get_comment(_id):
    try:
        comment = app.gradebook.find_comment_by_id(_id)
    except MissingEntry:
        abort(404)

    if request.method == "PUT":
        comment.comment = request.json.get("comment", None)
        app.gradebook.db.commit()

    return json.dumps(comment.to_dict())


app.register_blueprint(blueprint, url_defaults={'name': ''})
if __name__ == "__main__":
    app.run(debug=True)
