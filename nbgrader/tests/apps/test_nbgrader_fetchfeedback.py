import os
import sys
from os.path import join, exists, isfile

from ...utils import remove, notebook_hash
from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows


class TestNbGraderFetchFeedback(BaseTestApp):

    def _assign(self, assignment, course_dir, db, course="abc101"):
        run_nbgrader([
            "assign", assignment,
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
    
    @notwindows
    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["fetch_feedback", "--help-all"])

    @notwindows
    def test_single_file(self, db, course_dir, exchange, cache):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name="ps1")]\n""")
        self._assign("ps1", course_dir, db)
        self._release_and_fetch("ps1", exchange, cache, course_dir)
        self._submit("ps1", exchange, cache)
        self._collect("ps1", exchange)
        run_nbgrader(["autograde", "ps1", "--create", "--db", db])
        run_nbgrader(["generate_feedback", "ps1", "--db", db])
        run_nbgrader(["release_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        run_nbgrader(["fetch_feedback", "ps1", "--Exchange.root={}".format(exchange), '--course', 'abc101'])
        assert os.path.isdir(join("ps1", "feedback"))
        username = os.environ["USER"]
        timestamp = open(join(course_dir, "submitted", username, "ps1", "timestamp.txt")).read()
        assert os.path.isdir(join("ps1", "feedback", timestamp))
        assert os.path.isfile(join("ps1", "feedback", timestamp, 'p1.html'))
        assert os.path.isfile(join("ps1", "feedback", timestamp, 'p1.html'))
