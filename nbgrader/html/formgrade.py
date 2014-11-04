import json
import os

from flask import Flask, request, abort, redirect, url_for, render_template
app = Flask(__name__, static_url_path='/static')


@app.route("/fonts/<filename>")
def fonts(filename):
    return redirect(url_for('static', filename=os.path.join("fonts", filename)))


@app.route("/")
def home():
    return redirect('/assignments/')


@app.route("/assignments/")
def view_assignments():
    assignments = [x.to_dict() for x in app.gradebook.assignments]
    for assignment in assignments:
        all_notebooks = app.gradebook.find_notebooks(assignment=assignment["_id"])
        assignment['num_submissions'] = len(set([x.student for x in all_notebooks]))
        assignment.update(app.gradebook.avg_assignment_score(assignment["_id"]))
    return render_template("assignments.tpl", assignments=assignments)


@app.route("/assignments/<assignment_id>/")
def view_assignment(assignment_id):
    assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    notebooks = app.gradebook.avg_notebook_scores(assignment)
    return render_template(
        "assignment_notebooks.tpl",
        assignment=assignment,
        notebooks=notebooks)


@app.route("/assignments/<assignment_id>/<notebook_id>/")
def view_assignment_notebook(assignment_id, notebook_id):
    assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    submissions = app.gradebook.get_assignment_notebooks(assignment)[notebook_id]
    submissions = [x.to_dict() for x in submissions]
    for submission in submissions:
        score = app.gradebook.notebook_score(submission["_id"])
        submission.update(score)
        student = app.gradebook.find_student(_id=submission["student"])
        submission["student"] = student.to_dict()

    return render_template(
        "notebook_submissions.tpl",
        notebook_id=notebook_id,
        assignment=assignment,
        submissions=submissions)


@app.route("/assignments/<assignment_id>/<notebook_id>/<student_id>")
def view_submission(assignment_id, notebook_id, student_id):
    assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    student = app.gradebook.find_student(student_id=student_id)
    notebook = app.gradebook.find_notebook(
        assignment=assignment,
        student=student,
        notebook_id=notebook_id)

    filename = os.path.join(app.notebook_dir, app.notebook_dir_format.format(
        assignment_id=assignment.assignment_id,
        notebook_id=notebook.notebook_id,
        student_id=student.student_id))

    if not os.path.exists(filename):
        print filename
        abort(404)

    students = [s.student_id for s in app.gradebook.students]
    ix = students.index(student_id)
    if ix == 0:
        prev_student = None
    else:
        prev_student = students[ix - 1]
    if ix == (len(students) - 1):
        next_student = None
    else:
        next_student = students[ix + 1]

    resources = {
        'assignment_id': assignment.assignment_id,
        'student_id': student.student_id,
        'notebook_id': notebook.notebook_id,
        'notebook_uuid': notebook._id,
        'next': next_student,
        'prev': prev_student
    }

    output, resources = app.exporter.from_filename(filename, resources=resources)
    return output


@app.route("/api/notebook/<_id>/grades")
def get_all_grades(_id):
    notebook = app.gradebook.find_notebook(_id=_id)
    grades = app.gradebook.find_grades(notebook=notebook)
    return json.dumps([x.to_dict() for x in grades])


@app.route("/api/notebook/<_id>/comments")
def get_all_comments(_id):
    notebook = app.gradebook.find_notebook(_id=_id)
    comments = app.gradebook.find_comments(notebook=notebook)
    return json.dumps([x.to_dict() for x in comments])


@app.route("/api/grade/<_id>", methods=["GET", "PUT"])
def get_grade(_id):
    grade = app.gradebook.find_grade(_id=_id)
    if request.method == "PUT":
        grade.score = request.json.get("score", None)
        app.gradebook.update_grade(grade)
    return grade.to_json()


@app.route("/api/comment/<_id>", methods=["GET", "PUT"])
def get_comment(_id):
    comment = app.gradebook.find_comment(_id=_id)
    if request.method == "PUT":
        comment.comment = request.json.get("comment", None)
        app.gradebook.update_comment(comment)
    return comment.to_json()


if __name__ == "__main__":
    app.run(debug=True)
