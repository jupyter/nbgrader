import json
import os
from bson.objectid import ObjectId

from flask import Flask, request, abort, redirect, url_for
app = Flask(__name__, static_url_path='/static')


def jsonify(obj):
    if "_id" in obj:
        obj["_id"] = str(obj["_id"])
    return obj


@app.route("/<nb>")
def notebook(nb):
    filename = os.path.join(app.notebook_dir, "{}.html".format(nb))
    if not os.path.exists(filename):
        abort(404)
    with open(filename, "r") as fh:
        contents = fh.read()
    return contents


@app.route("/fonts/<filename>")
def fonts(filename):
    return redirect(url_for('static', filename=os.path.join("fonts", filename)))


@app.route("/<student>/<nb>/grades")
def get_all_grades(student, nb):
    return json.dumps([jsonify(x) for x in app.grades.find({
        "notebook": nb,
        "student_id": student
    })])


@app.route("/<student>/<nb>/comments")
def get_all_comments(student, nb):
    return json.dumps([jsonify(x) for x in app.comments.find({
        "notebook": nb,
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
