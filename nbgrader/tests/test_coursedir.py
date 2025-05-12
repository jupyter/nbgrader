import pytest
import os
import re
from pathlib import Path

from traitlets.config import Config

from nbgrader.coursedir import CourseDirectory


@pytest.fixture
def conf(course_dir):
    conf = Config()
    conf.CourseDirectory.root = course_dir
    return conf


def test_coursedir_configurable(conf, course_dir):
    coursedir = CourseDirectory(config=conf)
    assert coursedir.root == course_dir


@pytest.mark.parametrize("root", [None, os.path.sep + "[special]~root"])
def test_coursedir_format_path(conf, root):
    if root is not None:
        conf.CourseDirectory.root = root
    coursedir = CourseDirectory(config=conf)

    # The default includes the un-escaped root
    path = os.path.join(coursedir.root, "step", "student_id", "assignment1")
    assert coursedir.format_path("step", "student_id", "assignment1") == path

    # The escape=True option escapes the root and path separators
    escaped = Path(re.escape(coursedir.root))
    expected = escaped.anchor + re.escape(os.path.sep).join(
        (escaped / "step" / "student_id" / "(?P<assignment_id>.*)").parts[1:])

    actual = coursedir.format_path("step", "student_id", "(?P<assignment_id>.*)", escape=True)
    assert actual == expected

    # The escape=True option produces a regex pattern which can match paths
    match = re.match(actual, path)
    assert match is not None
    assert match.group("assignment_id") == "assignment1"
