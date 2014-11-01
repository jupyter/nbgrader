import json
import os

from flask import Flask, request, abort, redirect, url_for, render_template
app = Flask(__name__, static_url_path='/static')


def get_notebook_score(_id):
    score = 0
    max_score = 0
    needs_manual_grade = False

    notebook = app.gradebook.find_notebook(_id=_id)
    grades = app.gradebook.find_grades(notebook=notebook)
    for grade in grades:
        if grade.score is not None:
            score += grade.score
        elif grade.autoscore is not None:
            score += grade.autoscore
        else:
            needs_manual_grade = True

        if grade.max_score is not None:
            max_score += grade.max_score

    return {
        "score": score,
        "max_score": max_score,
        "needs_manual_grade": needs_manual_grade
    }


@app.route("/fonts/<filename>")
def fonts(filename):
    return redirect(url_for('static', filename=os.path.join("fonts", filename)))


@app.route("/")
def home():
    return render_template("assignment_list.tpl")


@app.route("/assignments")
def view_assignments():
    return redirect('/')


@app.route("/assignments/<assignment_id>/")
def view_assignment(assignment_id):
    assignment = app.gradebook.find_assignment(assignment_id=assignment_id)
    return render_template(
        "notebook_list.tpl",
        assignment_id=assignment.assignment_id,
        assignment_uuid=assignment._id)


@app.route("/assignments/<assignment_id>/<notebook_id>")
def view_notebook(assignment_id, notebook_id):
    filename = os.path.join(app.notebook_dir, notebook_id)
    if not os.path.exists(filename):
        abort(404)

    output, resources = app.exporter.from_filename(filename, resources={})
    return output


@app.route("/api/assignments")
def get_assignments():
    assignments = [x.to_dict() for x in app.gradebook.assignments]
    return json.dumps(assignments)


@app.route("/api/assignment/<_id>/notebooks")
def get_notebooks(_id):
    assignment = app.gradebook.find_assignment(_id=_id)
    notebooks = [x.to_dict() for x in app.gradebook.find_notebooks(assignment=assignment)]
    for nb in notebooks:
        nb.update(get_notebook_score(nb["_id"]))
        student = app.gradebook.find_student(_id=nb["student"])
        nb["student_name"] = "{last_name}, {first_name}".format(**student.to_dict())
        nb["student_id"] = student.student_id
        nb["path"] = "/assignments/{}/{}.ipynb".format(assignment.assignment_id, nb["notebook_id"])
    return json.dumps(notebooks)


@app.route("/api/notebook/<_id>/next")
def next_notebook(_id):
    ids = [x._id for x in app.gradebook.notebooks]
    index = ids.index(_id)
    if index == (len(ids) - 1):
        return json.dumps(None)
    nb = app.gradebook.find_notebook(_id=ids[index + 1]).to_dict()
    assignment = app.gradebook.find_assignment(_id=nb['assignment'])
    nb["path"] = "/assignments/{}/{}.ipynb".format(assignment.assignment_id, nb["notebook_id"])
    return json.dumps(nb)


@app.route("/api/notebook/<_id>/prev")
def prev_notebook(_id):
    ids = [x._id for x in app.gradebook.notebooks]
    index = ids.index(_id)
    if index == 0:
        return json.dumps(None)
    nb = app.gradebook.find_notebook(_id=ids[index - 1]).to_dict()
    assignment = app.gradebook.find_assignment(_id=nb['assignment'])
    nb["path"] = "/assignments/{}/{}.ipynb".format(assignment.assignment_id, nb["notebook_id"])
    return json.dumps(nb)


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
