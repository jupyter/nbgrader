import os
import sys
from os.path import join, exists, isfile

from ...utils import remove, notebook_hash
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderReleaseFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["release_feedback", "--help-all"])

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
        run_nbgrader(["feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1",  "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        nb_hash = notebook_hash(nb_path)
        assert exists(join(exchange, "abc101", "feedback", "{}.html".format(nb_hash)))


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
        run_nbgrader(["feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1",  "--Exchange.root={}".format(exchange), '--course', 'abc101'])

        if sys.platform == 'win32':
            perms = '711'  # not sure what it should be ....
        else:
            perms = '711'

        feedback_dir = join(exchange, "abc101", "feedback")
        assert self._get_permissions(feedback_dir) == perms

