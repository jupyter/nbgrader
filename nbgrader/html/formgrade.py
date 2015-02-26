import json
import os
import urllib

# python 3 compatibility
try:
    quote_plus = urllib.quote_plus
except AttributeError:
    quote_plus = urllib.parse.quote_plus


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
    assignments = [x.to_dict() for x in app.gradebook.assignments]
    assignments.sort(key=lambda x: x['assignment_id'])
    for assignment in assignments:
        all_notebooks = app.gradebook.find_notebooks(assignment=assignment["_id"])
        assignment['num_submissions'] = len(set([x.student for x in all_notebooks]))
        assignment.update(app.gradebook.avg_assignment_score(assignment["_id"]))
    return render_template("assignments.tpl", assignments=assignments)

@app.route("/students/")
def view_students():
    students = [x.to_dict() for x in app.gradebook.students]
    students.sort(key=lambda x: x["last_name"])
    for student in students:
        student.update(app.gradebook.student_score(student["_id"]))
    return render_template("students.tpl", students=students)

@app.route("/assignments/<assignment_id>/")
def view_assignment(assignment_id):
    try:
        assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    except ValueError:
        abort(404)

    notebooks = app.gradebook.avg_notebook_scores(assignment)
    notebooks.sort(key=lambda x: x['notebook_id'])
    return render_template(
        "assignment_notebooks.tpl",
        assignment=assignment,
        notebooks=notebooks)

@app.route("/students/<student_id>/")
def view_student(student_id):
    try:
        student = app.gradebook.find_student(student_id=student_id)
    except ValueError:
        abort(404)

    assignments = [x.to_dict() for x in app.gradebook.assignments]
    assignments.sort(key=lambda x: x['assignment_id'])
    for assignment in assignments:
        score = app.gradebook.assignment_score(assignment["_id"], student)
        if score:
            assignment.update(score)
        else:
            assignment['score'] = None

    return render_template(
        "student_assignments.tpl",
        assignments=assignments,
        student=student)

@app.route("/assignments/<assignment_id>/<notebook_id>/")
def view_assignment_notebook(assignment_id, notebook_id):
    try:
        assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    except ValueError:
        abort(404)

    students = app.gradebook.students
    submissions = []
    for student in students:
        try:
            submission = app.gradebook.find_notebook(
                assignment=assignment,
                student=student,
                notebook_id=notebook_id)
        except ValueError:
            continue

        submission = submission.to_dict()
        score = app.gradebook.notebook_score(submission["_id"])
        submission.update(score)
        submissions.append(submission)

    submissions.sort(key=lambda x: x["_id"])
    for i, submission in enumerate(submissions):
        submission["index"] = i

    return render_template(
        "notebook_submissions.tpl",
        notebook_id=notebook_id,
        assignment=assignment,
        submissions=submissions)

@app.route("/students/<student_id>/<assignment_id>/")
def view_student_assignment(student_id, assignment_id):
    try:
        student = app.gradebook.find_student(student_id=student_id)
        assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    except ValueError:
        abort(404)

    notebooks = app.gradebook.find_notebooks(student=student, assignment=assignment)
    submissions = []
    for notebook in notebooks:
        submission = notebook.to_dict()
        score = app.gradebook.notebook_score(submission["_id"])
        submission.update(score)
        submissions.append(submission)

    submissions.sort(key=lambda x: x['notebook_id'])

    return render_template(
        "student_submissions.tpl",
        assignment_id=assignment_id,
        student=student.to_dict(),
        submissions=submissions
    )

@app.route("/submissions/<submission_id>/<path:path>")
def view_submission_files(submission_id, path):
    try:
        submission = app.gradebook.find_notebook(_id=submission_id)
        assignment = app.gradebook.find_assignment(_id=submission.assignment)
        student = app.gradebook.find_student(_id=submission.student)
    except ValueError:
        abort(404)

    filename = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        assignment_id=assignment.assignment_id,
        notebook_id=submission.notebook_id,
        student_id=student.student_id))

    dirname = os.path.split(filename)[0]
    return send_from_directory(dirname, path)


@app.route("/submissions/<submission_id>/")
def view_submission(submission_id):
    try:
        submission = app.gradebook.find_notebook(_id=submission_id)
        assignment = app.gradebook.find_assignment(_id=submission.assignment)
        student = app.gradebook.find_student(_id=submission.student)
    except ValueError:
        abort(404)

    filename = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        assignment_id=assignment.assignment_id,
        notebook_id=submission.notebook_id,
        student_id=student.student_id))

    if not os.path.exists(filename):
        abort(404)

    submissions = sorted([x._id for x in app.gradebook.find_notebooks(
        assignment=assignment, notebook_id=submission.notebook_id)])

    ix = submissions.index(submission._id)
    if ix == 0:
        prev_submission = None
    else:
        prev_submission = submissions[ix - 1]
    if ix == (len(submissions) - 1):
        next_submission = None
    else:
        next_submission = submissions[ix + 1]

    resources = {
        'assignment_id': assignment.assignment_id,
        'notebook_id': submission.notebook_id,
        'submission_id': submission._id,
        'next': next_submission,
        'prev': prev_submission,
        'index': ix,
        'total': len(submissions),
        'notebook_path': "http://localhost:{}/notebooks/{}".format(
            app.notebook_server_port,
            os.path.relpath(filename, app.notebook_dir))
    }

    output, resources = app.exporter.from_filename(filename, resources=resources)
    return output


@app.route("/api/notebook/<_id>/grades")
def get_all_grades(_id):
    try:
        notebook = app.gradebook.find_notebook(_id=_id)
    except ValueError:
        abort(404)
    grades = app.gradebook.find_grades(notebook=notebook)
    return json.dumps([x.to_dict() for x in grades])


@app.route("/api/notebook/<_id>/comments")
def get_all_comments(_id):
    try:
        notebook = app.gradebook.find_notebook(_id=_id)
    except ValueError:
        abort(404)
    comments = app.gradebook.find_comments(notebook=notebook)
    return json.dumps([x.to_dict() for x in comments])


@app.route("/api/grade/<_id>", methods=["GET", "PUT"])
def get_grade(_id):
    try:
        grade = app.gradebook.find_grade(_id=_id)
    except ValueError:
        abort(404)
    if request.method == "PUT":
        grade.score = request.json.get("score", None)
        app.gradebook.update_grade(grade)
    return grade.to_json()


@app.route("/api/comment/<_id>", methods=["GET", "PUT"])
def get_comment(_id):
    try:
        comment = app.gradebook.find_comment(_id=_id)
    except ValueError:
        abort(404)
    if request.method == "PUT":
        comment.comment = request.json.get("comment", None)
        app.gradebook.update_comment(comment)
    return comment.to_json()


if __name__ == "__main__":
    app.run(debug=True)
