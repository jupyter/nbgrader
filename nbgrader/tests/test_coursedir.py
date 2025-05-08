import pytest
import os

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


def test_coursedir_format_path(conf):
    coursedir = CourseDirectory(config=conf)

    expected = os.path.join(coursedir.root, "step", "student_id", "assignment_id")
    assert coursedir.format_path("step", "student_id", "assignment_id") == expected

    expected = os.path.join(coursedir.root.replace("-", r"\-"), "step", "student_id", "assignment_id")
    assert coursedir.format_path("step", "student_id", "assignment_id", escape=True) == expected


def test_coursedir_format_path_with_specials(conf):
    conf.CourseDirectory.root = "/[test] root"
    coursedir = CourseDirectory(config=conf)

    expected = os.path.join("/[test] root", "step", "student_id", "assignment_id")
    assert coursedir.format_path("step", "student_id", "assignment_id") == expected

    expected = os.path.join(r"/\[test\]\ root", "step", "student_id", "assignment_id")
    assert coursedir.format_path("step", "student_id", "assignment_id", escape=True) == expected
