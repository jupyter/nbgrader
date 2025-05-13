import pytest
import os
import re
from pathlib import Path

from traitlets.config import Config

from nbgrader.coursedir import CourseDirectory

def pluck(key, collection):
    return sorted([x[key] for x in collection], key=lambda x: x)

def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

@pytest.mark.parametrize("root", [
    None, # Keep the course_dir fixture
    os.path.sep + "[special]~root",
    "C:\\Users\\Student",
])
def test_coursedir_format_path(course_dir, root):
    config = Config()
    if root is None:
        root = course_dir
    config.CourseDirectory.root = root
    coursedir = CourseDirectory(config=config)

    # The default includes the un-escaped root
    path = os.path.join(coursedir.root, "step", "student_id", "assignment1")
    assert coursedir.format_path("step", "student_id", "assignment1") == path

    # The escape=True option escapes the root and path separators
    root = Path(coursedir.root)
    expected = re.escape(root.anchor) + re.escape(os.path.sep).join([
        *[re.escape(part) for part in root.parts[1:]],
        "step", "student_id", "(?P<assignment_id>.*)"
    ])

    actual = coursedir.format_path("step", "student_id", "(?P<assignment_id>.*)", escape=True)
    assert actual == expected

    # The escape=True option produces a regex pattern which can match paths
    match = re.match(actual, path)
    assert match is not None
    assert match.group("assignment_id") == "assignment1"

def test_find_assignments(course_dir):
    config = Config({"CourseDirectory": {"root": course_dir}})
    coursedir = CourseDirectory(config=config)

    root = Path(coursedir.root)

    root.joinpath("source", ".", "assn").mkdir(parents=True)
    root.joinpath("release", ".", "assn").mkdir(parents=True)
    root.joinpath("submitted", "student1", "assn").mkdir(parents=True)
    root.joinpath("submitted", "student2", "assn").mkdir(parents=True)
    root.joinpath("autograded", "student1", "assn").mkdir(parents=True)
    root.joinpath("autograded", "student2", "assn").mkdir(parents=True)
    root.joinpath("feedback", "student1", "assn").mkdir(parents=True)
    root.joinpath("feedback", "student2", "assn").mkdir(parents=True)


    assert pluck("assignment_id", coursedir.find_assignments("source", ".")) == [
        "assn",
    ]

    assert pluck("student_id", coursedir.find_assignments("submitted")) == [
        "student1", "student2",
    ]

    assert pluck("nbgrader_step", coursedir.find_assignments(student_id="student1")) == [
        "autograded", "feedback", "submitted",
    ]

    # Finding by assignment has the shortcoming of not being able to find across
    # student_id="." and student_id="*" at the same time.
    assn = coursedir.find_assignments(assignment_id="assn", student_id=".")
    assert pluck("nbgrader_step", assn) == ["release", "source"]

    assn = coursedir.find_assignments(assignment_id="assn")
    assert pluck("nbgrader_step", assn) == [
        "autograded", "autograded", "feedback", "feedback", "submitted", "submitted",
    ]

def test_find_notebooks(course_dir):
    config = Config({"CourseDirectory": {"root": course_dir}})
    coursedir = CourseDirectory(config=config)

    root = Path(coursedir.root)

    touch(root.joinpath("source", ".", "assn", "assn.ipynb"))
    touch(root.joinpath("release", ".", "assn", "assn.ipynb"))
    touch(root.joinpath("submitted", "student1", "assn", "assn.ipynb"))
    touch(root.joinpath("submitted", "student2", "assn", "assn.ipynb"))
    touch(root.joinpath("autograded", "student1", "assn", "assn.ipynb"))
    touch(root.joinpath("autograded", "student2", "assn", "assn.ipynb"))
    touch(root.joinpath("feedback", "student1", "assn", "assn.html"))
    touch(root.joinpath("feedback", "student2", "assn", "assn.html"))

    assert pluck("ext", coursedir.find_notebooks(assignment_id="assn", ext="*")) == [
        "html",
        "html",
        "ipynb",
        "ipynb",
        "ipynb",
        "ipynb",
    ]


    # By default, we only look for .ipynb files
    assert pluck("nbgrader_step", coursedir.find_notebooks(student_id="student1")) == [
        "autograded", "submitted",
    ]

    assert pluck("nbgrader_step", coursedir.find_notebooks(student_id="student1", ext="*")) == [
        "autograded", "feedback", "submitted",
    ]

