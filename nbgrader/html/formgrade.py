from flask import Flask, request
app = Flask(__name__, static_url_path='/static')

import json
from bson.objectid import ObjectId

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client['assignments']
grades = db['grades']
comments = db['comments']


def jsonify(obj):
    if "_id" in obj:
        obj["_id"] = str(obj["_id"])
    return obj


@app.route("/<student>/<nb>")
def hello(student, nb):
    return app.send_static_file("{}.html".format(nb))


@app.route("/<student>/<nb>/grades")
def get_all_grades(student, nb):
    return json.dumps([jsonify(x) for x in grades.find({
        "notebook": nb,
        "student_id": student
    })])


@app.route("/<student>/<nb>/comments")
def get_all_comments(student, nb):
    return json.dumps([jsonify(x) for x in comments.find({
        "notebook": nb,
        "student_id": student
    })])


@app.route("/grades/<_id>", methods=["GET", "PUT"])
def get_grade(_id):
    grade_id = {"_id": ObjectId(_id)}
    if request.method == "PUT":
        grades.update(grade_id, {"$set": {
            "score": request.json.get("score", None)
        }})
    return json.dumps(jsonify(grades.find_one(grade_id)))


@app.route("/comments/<_id>", methods=["GET", "PUT"])
def get_comment(_id):
    comment_id = {"_id": ObjectId(_id)}
    if request.method == "PUT":
        comments.update(comment_id, {"$set": {
            "comment": request.json.get("comment", None)
        }})
    return json.dumps(jsonify(comments.find_one(comment_id)))


if __name__ == "__main__":
    app.run(debug=True)
