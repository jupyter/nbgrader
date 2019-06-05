import os
import sys
from os.path import join, exists, isfile

from ...utils import remove, notebook_hash
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
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name="ps1")]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo")]\n""")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))
        
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        nb_hash = notebook_hash(nb_path)
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))
        # release feedback shoul overwrite without error
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

    @notwindows
    def test_single_student(self, db, course_dir, exchange):
        """Can feedback be generated for an unchanged assignment?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name="ps1")]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo")]\n""")
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
        nb_hash = notebook_hash(nb_path)
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))
        nb_hash2 = notebook_hash(nb_path2)
        assert not exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash2)))
        # release feedback shoul overwrite without error
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

    @notwindows
    def test_permissions(self, db, course_dir, exchange):
        """Are permissions properly set?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name="ps1")]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo")]\n""")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        self._copy_file(join("files", "timestamp.txt"), join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"))

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])

        perms = '711'

        feedback_dir = join(exchange, "abc101", "feedback")
        assert self._get_permissions(feedback_dir) == perms
