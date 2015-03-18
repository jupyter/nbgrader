import json
import os
from nbgrader.api import MissingEntry
from flask import Flask, request, abort, redirect, url_for, render_template, send_from_directory

app = Flask(__name__, static_url_path='')


@app.route("/static/<path:filename>")
def static_proxy(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


@app.route("/fonts/<filename>")
def fonts(filename):
    return redirect(url_for('static', filename=os.path.join("fonts", filename)))


@app.route("/")
def home():
    return redirect('/assignments/')


@app.route("/assignments/")
def view_assignments():
    assignments = []
    for assignment in app.gradebook.assignments:
        x = assignment.to_dict()
        x["average_score"] = app.gradebook.average_assignment_score(assignment.name)
        x["average_code_score"] = app.gradebook.average_assignment_code_score(assignment.name)
        x["average_written_score"] = app.gradebook.average_assignment_written_score(assignment.name)
        assignments.append(x)
    return render_template("assignments.tpl", assignments=assignments)

@app.route("/students/")
def view_students():
    students = app.gradebook.student_dicts()
    students.sort(key=lambda x: x["last_name"])
    return render_template("students.tpl", students=students)

@app.route("/assignments/<assignment_id>/")
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
        notebooks=notebooks)

@app.route("/students/<student_id>/")
def view_student(student_id):
    try:
        student = app.gradebook.find_student(student_id)
    except MissingEntry:
        abort(404)

    assignments = [x.to_dict() for x in student.submissions]
    assignments.sort(key=lambda x: x["duedate"])
    student = student.to_dict()

    return render_template(
        "student_assignments.tpl",
        assignments=assignments,
        student=student)

@app.route("/assignments/<assignment_id>/<notebook_id>/")
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
        submissions=submissions)

@app.route("/students/<student_id>/<assignment_id>/")
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
        submissions=submissions
    )

@app.route("/submissions/<submission_id>/<path:path>")
def view_submission_files(submission_id, path):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
        student_id = submission.student.id
    except MissingEntry:
        abort(404)

    filename = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        assignment_id=assignment_id,
        notebook_id=notebook_id,
        student_id=student_id))

    dirname = os.path.split(filename)[0]
    return send_from_directory(dirname, path)


@app.route("/submissions/<submission_id>/")
def view_submission(submission_id):
    try:
        submission = app.gradebook.find_submission_notebook_by_id(submission_id)
        assignment_id = submission.assignment.assignment.name
        notebook_id = submission.notebook.name
        student_id = submission.student.id
    except MissingEntry:
        abort(404)

    filename = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        assignment_id=assignment_id,
        notebook_id=notebook_id,
        student_id=student_id))

    if not os.path.exists(filename):
        abort(404)

    if not app.notebook_server_exists:
        abort(503, 'Submission viewing notebook server not started.')

    submissions = app.gradebook.notebook_submissions(notebook_id, assignment_id)
    submissions = sorted([x.id for x in submissions])

    ix = submissions.index(submission.id)
    if ix == 0:
        prev_submission = None
    else:
        prev_submission = submissions[ix - 1]
    if ix == (len(submissions) - 1):
        next_submission = None
    else:
        next_submission = submissions[ix + 1]

    resources = {
        'assignment_id': assignment_id,
        'notebook_id': notebook_id,
        'submission_id': submission.id,
        'next': next_submission,
        'prev': prev_submission,
        'index': ix,
        'total': len(submissions),
        'notebook_path': "http://{}:{}/notebooks/{}".format(
            app.notebook_server_ip,
            app.notebook_server_port,
            os.path.relpath(filename, app.notebook_dir))
    }

    output, resources = app.exporter.from_filename(filename, resources=resources)
    return output


@app.route("/api/grades")
def get_all_grades():
    submission_id = request.args["submission_id"]

    try:
        notebook = app.gradebook.find_submission_notebook_by_id(submission_id)
    except MissingEntry:
        abort(404)

    return json.dumps([g.to_dict() for g in notebook.grades])


@app.route("/api/comments")
def get_all_comments():
    submission_id = request.args["submission_id"]

    try:
        notebook = app.gradebook.find_submission_notebook_by_id(submission_id)
    except MissingEntry:
        abort(404)

    return json.dumps([c.to_dict() for c in notebook.comments])


@app.route("/api/grade/<_id>", methods=["GET", "PUT"])
def get_grade(_id):
    try:
        grade = app.gradebook.find_grade_by_id(_id)
    except MissingEntry:
        abort(404)

    if request.method == "PUT":
        grade.manual_score = request.json.get("manual_score", None)
        app.gradebook.db.commit()

    return json.dumps(grade.to_dict())


@app.route("/api/comment/<_id>", methods=["GET", "PUT"])
def get_comment(_id):
    try:
        comment = app.gradebook.find_comment_by_id(_id)
    except MissingEntry:
        abort(404)

    if request.method == "PUT":
        comment.comment = request.json.get("comment", None)
        app.gradebook.db.commit()

    return json.dumps(comment.to_dict())


if __name__ == "__main__":
    app.run(debug=True)
