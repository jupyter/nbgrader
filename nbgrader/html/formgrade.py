import json
import os
import glob

from flask import Flask, request, abort, redirect, url_for, render_template
app = Flask(__name__, static_url_path='/static')


def get_notebook_list():
    suffix = ".autograded.html"
    notebooks = glob.glob(os.path.join(app.notebook_dir, "*{}".format(suffix)))
    notebooks = [os.path.split(x)[1][:-len(suffix)] for x in notebooks]
    return sorted(notebooks)


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
    return render_template("notebook_list.html")


@app.route("/<nb>")
def notebook(nb):
    filename = os.path.join(app.notebook_dir, nb)
    if not os.path.exists(filename):
        abort(404)
    with open(filename, "r") as fh:
        contents = fh.read()
    return contents


@app.route("/api/notebooks")
def get_notebooks():
    notebooks = [x.to_dict() for x in app.gradebook.notebooks]
    for nb in notebooks:
        nb.update(get_notebook_score(nb["_id"]))
        student = app.gradebook.find_student(_id=nb["student"])
        nb["student_name"] = "{last_name}, {first_name}".format(**student.to_dict())
        nb["student_id"] = student.student_id
    return json.dumps(notebooks)


@app.route("/api/notebook/<_id>/next")
def next_notebook(_id):
    ids = [x._id for x in app.gradebook.notebooks]
    index = ids.index(_id)
    if index == (len(ids) - 1):
        return json.dumps(None)
    return app.gradebook.find_notebook(_id=ids[index + 1]).to_json()


@app.route("/api/notebook/<_id>/prev")
def prev_notebook(_id):
    ids = [x._id for x in app.gradebook.notebooks]
    index = ids.index(_id)
    if index == 0:
        return json.dumps(None)
    return app.gradebook.find_notebook(_id=ids[index - 1]).to_json()


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
