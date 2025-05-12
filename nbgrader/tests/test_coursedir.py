import pytest
import os
import re
from pathlib import Path

from traitlets.config import Config

from nbgrader.coursedir import CourseDirectory

@pytest.mark.parametrize("root", [
    None, # Keep the course_dir fixture
    os.path.sep + "[special]~root",
    "C:\\Users\\Student",
])
def test_coursedir_format_path(course_dir, root):
    conf = Config()
    if root is None:
        root = course_dir
    conf.CourseDirectory.root = root
    coursedir = CourseDirectory(config=conf)

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
