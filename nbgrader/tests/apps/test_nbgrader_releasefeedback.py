import os
import sys
from os.path import join, exists, isfile
import pytest

from ...utils import notebook_hash, make_unique_key
from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows


class TestNbGraderReleaseFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["release_feedback", "--help-all"])

    def test_second_argument(self):
        """Does the help display without error?"""
        run_nbgrader(["release_feedback", "ps1", "second_arg"], retcode=1)

    def test_no_argument(self):
        """Does the help display without error?"""
        run_nbgrader(["release_feedback"], retcode=1)

    @notwindows
    def test_single_file(self, db, course_dir, exchange):
        """Can feedback be generated for an unchanged assignment?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))

        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        unique_key = make_unique_key("abc101", "ps1", "p1", "foo", "2019-05-30 11:44:01.911849 UTC")
        nb_hash = notebook_hash(nb_path, unique_key)
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))
        # release feedback should overwrite without error
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

    @notwindows
    def test_single_student(self, db, course_dir, exchange):
        """Can feedback be generated for an unchanged assignment?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))
        nb_path2 = join(course_dir, "submitted", "bar", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-changed.ipynb"), nb_path2)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"))

        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101', '--student', 'foo'])
        unique_key = make_unique_key("abc101", "ps1", "p1", "foo", "2019-05-30 11:44:01.911849 UTC")
        nb_hash = notebook_hash(nb_path, unique_key)
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))
        unique_key2 = make_unique_key("abc101", "ps1", "p1", "bar", "2019-05-30 11:44:01.911849 UTC")
        nb_hash2 = notebook_hash(nb_path2, unique_key2)
        assert not exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash2)))
        # release feedback should overwrite without error
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

    @notwindows
    def test_student_id_exclude(self, db, course_dir, exchange):
        """Does --CourseDirectory.student_id_exclude=X exclude students?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        run_nbgrader(["db", "student", "add", "baz", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))
        nb_path2 = join(course_dir, "submitted", "bar", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-changed.ipynb"), nb_path2)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"))

        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101',
                      "--CourseDirectory.student_id_exclude=bar,baz"]) # baz doesn't exist, test still OK though
        unique_key = make_unique_key("abc101", "ps1", "p1", "foo", "2019-05-30 11:44:01.911849 UTC")
        nb_hash = notebook_hash(nb_path, unique_key) # foo
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))
        unique_key2 = make_unique_key("abc101", "ps1", "p1", "bar", "2019-05-30 11:44:01.911849 UTC")
        nb_hash2 = notebook_hash(nb_path2, unique_key2) # bar
        assert not exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash2)))
        # release feedback should overwrite without error
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])


    @notwindows
    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, db, course_dir, exchange, groupshared):
        """Are permissions properly set?"""
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            if groupshared:
                fh.write("""c.CourseDirectory.groupshared = True\n""")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))
        unique_key = make_unique_key("abc101", "ps1", "p1", "foo", "2019-05-30 11:44:01.911849 UTC")
        nb_hash = notebook_hash(nb_path, unique_key)

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

        if groupshared:
            perms = '664'
            dirperms = '2771'
        else:
            perms = '644'
            dirperms = '711'

        feedback_dir = join(exchange, "abc101", "feedback")
        assert self._get_permissions(feedback_dir) == dirperms
        os.system("find %s -ls"%feedback_dir)
        assert self._get_permissions(join(feedback_dir, nb_hash+".html")) == perms
