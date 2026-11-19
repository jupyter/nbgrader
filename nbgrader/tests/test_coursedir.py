import re

import pytest
from traitlets import TraitError

from ..coursedir import CourseDirectory


@pytest.mark.parametrize("assignment_id", [
    "ps1",
    "123 (abc)",
    "hw {1}",
    "a.b$c^d",
    "ps 1 - part 2",
])
def test_assignment_id_allows_regex_special_characters(assignment_id):
    coursedir = CourseDirectory()
    coursedir.assignment_id = assignment_id
    assert coursedir.assignment_id == assignment_id


@pytest.mark.parametrize("assignment_id", [
    "foo+bar",
    "test 1/2",
    "test 1\\2",
    "123 [abc]",
    "123 [abc",
    "123 abc]",
])
def test_assignment_id_rejects_invalid_characters(assignment_id):
    coursedir = CourseDirectory()
    with pytest.raises(TraitError):
        coursedir.assignment_id = assignment_id


def test_assignment_id_strips_whitespace():
    coursedir = CourseDirectory()
    coursedir.assignment_id = "  ps1 "
    assert coursedir.assignment_id == "ps1"


@pytest.mark.parametrize("assignment_id", ["ps1", "123 (abc)", "hw {1}", "a.b$c^d"])
def test_format_path_escape_matches_escaped_assignment_id(tmp_path, assignment_id):
    coursedir = CourseDirectory(root=str(tmp_path))
    path = coursedir.format_path(coursedir.submitted_directory, "foo", assignment_id)
    regex = coursedir.format_path(
        coursedir.submitted_directory,
        "(?P<student_id>.*)",
        re.escape(assignment_id),
        escape=True)
    match = re.match(regex, path)
    assert match is not None
    assert match.group("student_id") == "foo"
