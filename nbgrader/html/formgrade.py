import json
import os
import glob
from bson.objectid import ObjectId

from flask import Flask, request, abort, redirect, url_for, render_template
app = Flask(__name__, static_url_path='/static')


def jsonify(obj):
    if "_id" in obj:
        obj["_id"] = str(obj["_id"])
    return obj


def get_notebook_list():
    suffix = ".autograded.html"
    notebooks = glob.glob(os.path.join(app.notebook_dir, "*{}".format(suffix)))
    notebooks = [os.path.split(x)[1][:-len(suffix)] for x in notebooks]
    return sorted(notebooks)

@app.route("/")
def list_notebooks():
    notebooks = get_notebook_list()
    return render_template("notebook_list.html", notebooks=notebooks)


@app.route("/<nb>")
def notebook(nb):
    filename = os.path.join(app.notebook_dir, "{}.autograded.html".format(nb))
    if not os.path.exists(filename):
        abort(404)
    with open(filename, "r") as fh:
        contents = fh.read()
    return contents


@app.route("/<nb>/next")
def next_notebook(nb):
    notebooks = get_notebook_list()
    index = notebooks.index(nb)
    if index == (len(notebooks) - 1):
        return json.dumps(None)
    return json.dumps(notebooks[index + 1])


@app.route("/<nb>/prev")
def prev_notebook(nb):
    notebooks = get_notebook_list()
    index = notebooks.index(nb)
    if index == 0:
        return json.dumps(None)
    return json.dumps(notebooks[index - 1])


@app.route("/fonts/<filename>")
def fonts(filename):
    return redirect(url_for('static', filename=os.path.join("fonts", filename)))


@app.route("/<student>/<nb>/grades")
def get_all_grades(student, nb):
    return json.dumps([jsonify(x) for x in app.grades.find({
        "notebook_id": nb,
        "student_id": student
    })])


@app.route("/<student>/<nb>/comments")
def get_all_comments(student, nb):
    return json.dumps([jsonify(x) for x in app.comments.find({
        "notebook_id": nb,
        "student_id": student
    })])


@app.route("/grades/<_id>", methods=["GET", "PUT"])
def get_grade(_id):
    grade_id = {"_id": ObjectId(_id)}
    if request.method == "PUT":
        app.grades.update(grade_id, {"$set": {
            "score": request.json.get("score", None)
        }})
    return json.dumps(jsonify(app.grades.find_one(grade_id)))


@app.route("/comments/<_id>", methods=["GET", "PUT"])
def get_comment(_id):
    comment_id = {"_id": ObjectId(_id)}
    if request.method == "PUT":
        app.comments.update(comment_id, {"$set": {
            "comment": request.json.get("comment", None)
        }})
    return json.dumps(jsonify(app.comments.find_one(comment_id)))


if __name__ == "__main__":
    app.run(debug=True)
