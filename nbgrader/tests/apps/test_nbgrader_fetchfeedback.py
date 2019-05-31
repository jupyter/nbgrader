import os
import sys
from os.path import join, exists, isfile

from ...utils import remove, notebook_hash
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderFetchFeedback(BaseTestApp):

    def _assign(self, assignment, course_dir, db, course="abc101"):
        run_nbgrader([
            "assign", assignment,
            #"--course", course,
            "--db", db
        ])

    def _release(self, assignment, exchange, cache, course_dir, course="abc101"):
        run_nbgrader([
            "release", assignment,
            "--course", course,
            "--Exchange.cache={}".format(cache),
            "--Exchange.root={}".format(exchange)
        ])

    def _fetch(self, assignment, exchange, cache, course="abc101", flags=None):
        cmd = [
            "fetch", assignment,
            "--course", course,
            "--Exchange.cache={}".format(cache),
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_nbgrader(cmd)

    def _release_and_fetch(self, assignment, exchange, cache, course_dir, course="abc101"):
        self._release(assignment, exchange, cache, course_dir, course=course)
        self._fetch(assignment, exchange, cache, course=course)

    def _submit(self, assignment, exchange, cache, flags=None, retcode=0, course="abc101"):
        cmd = [
            "submit", assignment,
            "--course", course,
            "--Exchange.cache={}".format(cache),
            "--Exchange.root={}".format(exchange),
        ]

        if flags is not None:
            cmd.extend(flags)

        run_nbgrader(cmd, retcode=retcode)

    def _collect(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "collect", assignment,
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_nbgrader(cmd, retcode=retcode)
    
    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["fetchfeedback", "--help-all"])

    def test_single_file(self, db, course_dir, exchange, cache):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name="ps1")]\n""")
        #    fh.write("""c.CourseDirectory.db_students = [dict(id="foo")]\n""")
        self._assign("ps1", course_dir, db)
        self._release_and_fetch("ps1", exchange, cache, course_dir)
        self._submit("ps1", exchange, cache)
        self._collect("ps1", exchange)
        #self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        #run_nbgrader(["assign", "ps1", "--db", db])
        #nb_path = join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        #self._copy_file(join("files", "submitted-unchanged.ipynb"), nb_path)
        run_nbgrader(["autograde", "ps1", "--create","--db", db])
        run_nbgrader(["feedback", "ps1", "--db", db])
        run_nbgrader(["releasefeedback", "ps1",  "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        run_nbgrader(["fetchfeedback", "ps1",  "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        assert os.path.isdir(join("ps1", "feedback"))
        username = os.environ["USER"]
        timestamp = open(join(course_dir, "submitted", username , "ps1", "timestamp.txt")).read()
        assert os.path.isdir(join("ps1", "feedback", timestamp))
        assert os.path.isfile(join("ps1", "feedback", timestamp, 'p1.html'))
        assert os.path.isfile(join("ps1", "feedback", timestamp, 'p1.html'))
        