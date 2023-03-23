# -*- coding: utf-8 -*-

import io
import os
import sys
import json
import pytest

from os.path import join
from textwrap import dedent
from nbformat import current_nbformat

from ...api import Gradebook, MissingEntry
from ...utils import remove
from ...nbgraderformat import reads
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderAutograde(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["autograde", "--help-all"])

    def test_missing_student(self, db, course_dir):
        """Is a missing student automatically created?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate", "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "baz", "ps1", "p1.ipynb"))

        # If we explicitly disable creating students, autograde should fail
        run_nbgrader(["autograde", "ps1", "--db", db, "--Autograde.create_student=False"], retcode=1)

        # The default is now to create missing students (formerly --create)
        run_nbgrader(["autograde", "ps1", "--db", db])

    def test_missing_assignment(self, db, course_dir):
        """Is an error thrown when the assignment is missing?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate", "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "ps2", "foo", "p1.ipynb"))
        run_nbgrader(["autograde", "ps2", "--db", db], retcode=1)

    def test_grade(self, db, course_dir):
        """Can files be graded?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate", "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            notebook = gb.find_submission_notebook("p1", "ps1", "foo")
            assert notebook.score == 1
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == False

            comment1 = gb.find_comment("set_a", "p1", "ps1", "foo")
            comment2 = gb.find_comment("baz", "p1", "ps1", "foo")
            comment3 = gb.find_comment("quux", "p1", "ps1", "foo")
            assert comment1.comment == "No response."
            assert comment2.comment == "No response."
            assert comment3.comment == "No response."

            notebook = gb.find_submission_notebook("p1", "ps1", "bar")
            assert notebook.score == 2
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == True

            comment1 = gb.find_comment("set_a", "p1", "ps1", "bar")
            comment2 = gb.find_comment("baz", "p1", "ps1", "bar")
            comment2 = gb.find_comment("quux", "p1", "ps1", "bar")
            assert comment1.comment == None
            assert comment2.comment == None

    def test_showtraceback_exploit(self, db, course_dir):
        """Can students exploit showtraceback to hide errors from all future cell outputs to receive free points for incorrect cells?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate", "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        run_nbgrader(["db", "student", "add", "spam", "--db", db])
        run_nbgrader(["db", "student", "add", "eggs", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        # This exploit previously caused cell executions that would indefinitely hang.
        # See: https://github.com/ipython/ipython/commit/fd34cf5
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.Execute.timeout = None""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-cheat-attempt.ipynb"), join(course_dir, "submitted", "spam", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-cheat-attempt-alternative.ipynb"), join(course_dir, "submitted", "eggs", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "spam", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "spam", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "eggs", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "eggs", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            notebook = gb.find_submission_notebook("p1", "ps1", "foo")
            assert notebook.score == 1
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == False

            notebook = gb.find_submission_notebook("p1", "ps1", "bar")
            assert notebook.score == 2
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == True

            notebook = gb.find_submission_notebook("p1", "ps1", "spam")
            assert notebook.score == 1
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == True

            notebook = gb.find_submission_notebook("p1", "ps1", "eggs")
            assert notebook.score == 1
            assert notebook.max_score == 7
            assert notebook.needs_manual_grade == True

    def test_student_id_exclude(self, db, course_dir):
        """Does --CourseDirectory.student_id_exclude=X exclude students?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "baz", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db, '--CourseDirectory.student_id_exclude=bar,baz'])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "baz", "ps1", "p1.ipynb"))

        with Gradebook(db) as gb:
            notebook = gb.find_submission_notebook("p1", "ps1", "foo")
            assert notebook.score == 1

            with pytest.raises(MissingEntry):
                notebook = gb.find_submission_notebook("p1", "ps1", "bar")
            with pytest.raises(MissingEntry):
                notebook = gb.find_submission_notebook("p1", "ps1", "baz")

    def test_grade_timestamp(self, db: str, course_dir: str) -> None:
        """Is a timestamp correctly read in?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-01 14:58:23.948203 America/Los_Angeles")

        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            submission = gb.find_submission("ps1", "foo")
            assert submission.total_seconds_late > 0
            submission = gb.find_submission("ps1", "bar")
            assert submission.total_seconds_late == 0

        # make sure it still works to run it a second time
        run_nbgrader(["autograde", "ps1", "--db", db])

    def test_grade_empty_timestamp(self, db: str, course_dir: str) -> None:
        """Issue #580 - Does the autograder handle empty or invalid timestamp
        strings"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])


        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "")
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            submission = gb.find_submission("ps1", "foo")
            assert submission.total_seconds_late == 0

        invalid_timestamp = "But I want to be a timestamp string :("
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), invalid_timestamp)
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

    def test_late_submission_penalty_none(self, db: str, course_dir: str) -> None:
        """Does 'none' method do nothing?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        # not late
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 14:58:23.948203 America/Los_Angeles")

        # 1h late
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")

        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            # not late
            submission = gb.find_submission("ps1", "foo")
            nb = submission.notebooks[0]
            assert nb.score == 1
            assert submission.total_seconds_late == 0
            assert nb.late_submission_penalty == None

            # 1h late
            submission = gb.find_submission("ps1", "bar")
            nb = submission.notebooks[0]
            assert nb.score == 2
            assert submission.total_seconds_late > 0
            assert nb.late_submission_penalty == None

    def test_late_submission_penalty_zero(self, db: str, course_dir: str) -> None:
        """Does 'zero' method assign notebook.score as penalty if late?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.LateSubmissionPlugin.penalty_method = 'zero'""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        # not late
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 14:58:23.948203 America/Los_Angeles")

        # 1h late
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")

        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            # not late
            submission = gb.find_submission("ps1", "foo")
            nb = submission.notebooks[0]
            assert nb.score == 1
            assert submission.total_seconds_late == 0
            assert nb.late_submission_penalty == None

            # 1h late
            submission = gb.find_submission("ps1", "bar")
            nb = submission.notebooks[0]
            assert nb.score == 2
            assert submission.total_seconds_late > 0
            assert nb.late_submission_penalty == nb.score

        # Issue 723 - check penalty is reset if timestamp changed
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-02 14:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "--force", "ps1", "--db", db])

        with Gradebook(db) as gb:
            # no longer late
            submission = gb.find_submission("ps1", "bar")
            nb = submission.notebooks[0]
            assert nb.score == 2
            assert submission.total_seconds_late == 0
            assert nb.late_submission_penalty == None

    def test_late_submission_penalty_plugin(self, db: str, course_dir: str) -> None:
        """Does plugin set 1 point per hour late penalty?"""

        plugin = dedent("""
        from __future__ import division
        from nbgrader.plugins import BasePlugin

        class Blarg(BasePlugin):
            def late_submission_penalty(self, student_id, score, total_seconds_late):
                # loss 1 mark per hour late
                hours_late = total_seconds_late / 3600
                return int(hours_late)
        """)

        with open("late_plugin.py", 'w') as fh:
            fh.write(plugin)

        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.AssignLatePenalties.plugin_class = 'late_plugin.Blarg'""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        # 4h late
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 18:58:23.948203 America/Los_Angeles")

        # 1h late
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")

        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        with Gradebook(db) as gb:
            # 4h late
            submission = gb.find_submission("ps1", "foo")
            nb = submission.notebooks[0]
            assert nb.score == 1
            assert submission.total_seconds_late > 0
            assert nb.late_submission_penalty == nb.score

            # 1h late
            submission = gb.find_submission("ps1", "bar")
            nb = submission.notebooks[0]
            assert nb.score == 2
            assert submission.total_seconds_late > 0
            assert nb.late_submission_penalty == 1

    def test_force(self, db: str, course_dir: str) -> None:
        """Ensure the force option works properly"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_nbgrader(["autograde", "ps1", "--db", db, "--force"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite
        remove(join(course_dir, "source", "ps1", "foo.txt"))
        remove(join(course_dir, "submitted", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db, "--force"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

    def test_force_f(self, db: str, course_dir: str) -> None:
        """Ensure the force option works properly"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_nbgrader(["autograde", "ps1", "--db", db, "-f"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite
        remove(join(course_dir, "source", "ps1", "foo.txt"))
        remove(join(course_dir, "submitted", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db, "-f"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

    def test_filter_notebook(self, db: str, course_dir: str) -> None:
        """Does autograding filter by notebook properly?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_nbgrader(["autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook still causes the autograder to run
        remove(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that running it again doesn"t do anything
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_nbgrader(["autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook doesn"t caus the autograder to run
        remove(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

    def test_grade_overwrite_files(self, db: str, course_dir: str) -> None:
        """Are dependent files properly linked and overwritten?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.Autograde.exclude_overwriting = {"ps1": ["helper.py"]}\n""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "data.csv"), "some,data\n")
        self._make_file(join(course_dir, "source", "ps1", "helper.py"), "print('hello!')\n")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data.csv"), "some,other,data\n")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "helper.py"), "print('this is different!')\n")
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data.csv"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "helper.py"))

        with open(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "r") as fh:
            contents = fh.read()
        assert contents == "2015-02-02 15:58:23.948203 America/Los_Angeles"

        with open(join(course_dir, "autograded", "foo", "ps1", "data.csv"), "r") as fh:
            contents = fh.read()
        assert contents == "some,data\n"

        with open(join(course_dir, "autograded", "foo", "ps1", "helper.py"), "r") as fh:
            contents = fh.read()
        assert contents == "print('this is different!')\n"

    def test_grade_overwrite_files_subdirs(self, db: str, course_dir: str) -> None:
        """Are dependent files properly linked and overwritten?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.Autograde.exclude_overwriting = {{"ps1": ["{}"]}}\n""".format(os.path.join("subdir", "helper.py")))

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "subdir", "data.csv"), "some,data\n")
        self._make_file(join(course_dir, "source", "ps1", "subdir", "helper.py"), "print('hello!')\n")
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "subdir", "data.csv"), "some,other,data\n")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "subdir", "helper.py"), "print('this is different!')\n")
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "subdir", "data.csv"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "subdir", "helper.py"))

        with open(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "r") as fh:
            contents = fh.read()
        assert contents == "2015-02-02 15:58:23.948203 America/Los_Angeles"

        with open(join(course_dir, "autograded", "foo", "ps1", "subdir", "data.csv"), "r") as fh:
            contents = fh.read()
        assert contents == "some,data\n"

        with open(join(course_dir, "autograded", "foo", "ps1", "subdir", "helper.py"), "r") as fh:
            contents = fh.read()
        assert contents == "print('this is different!')\n"

    def test_side_effects(self, db: str, course_dir: str) -> None:
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "side-effects.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "side-effects.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "side-effect.txt"))
        assert not os.path.isfile(join(course_dir, "submitted", "foo", "ps1", "side-effect.txt"))

    def test_skip_extra_notebooks(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1 copy.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1 copy.ipynb"))

    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, course_dir, groupshared):
        """Are permissions properly set?"""
        run_nbgrader(["db", "assignment", "add", "ps1"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])
        with open("nbgrader_config.py", "a") as fh:
            if groupshared:
                fh.write("""c.CourseDirectory.groupshared = True\n""")

        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "foo", "ps1", "foo.txt"), "foo")
        run_nbgrader(["autograde", "ps1"])

        if not groupshared:
            if sys.platform == 'win32':
                perms = '444'
            else:
                perms = '444'
        else:
            if sys.platform == 'win32':
                perms = '666'
                dirperms = '777'
            else:
                perms = '664'
                dirperms = '2775'

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        if groupshared:
            # non-groupshared doesn't make guarantees about directory perms
            assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1")) == dirperms
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb")) == perms
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.txt")) == perms

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "foo", "ps1", "foo.txt"), "foo")
        run_nbgrader(["autograde", "ps1", "--AutogradeApp.permissions=644"])

        if sys.platform == 'win32':
            perms = '666'
        else:
            perms = '644'

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb")) == perms
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.txt")) == perms

    def test_force_single_notebook(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1",
                      "--ClearMetadataPreprocessor.enabled=True",
                      "--ClearMetadataPreprocessor.clear_notebook_metadata=False",
                      "--ClearMetadataPreprocessor.preserve_cell_metadata_mask=[('nbgrader')]"
                      ])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        p1 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

    def test_update_newer(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 America/Los_Angeles"
        p = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 America/Los_Angeles"
        assert p != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

    def test_update_newer_single_notebook(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1",
                      "--ClearMetadataPreprocessor.enabled=True",
                      "--ClearMetadataPreprocessor.clear_notebook_metadata=False",
                      "--ClearMetadataPreprocessor.preserve_cell_metadata_mask=[('nbgrader')]"
                      ])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 America/Los_Angeles"
        p1 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 America/Los_Angeles")
        run_nbgrader(["autograde", "ps1", "--notebook", "p1"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 America/Los_Angeles"
        assert p1 != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

    def test_hidden_tests_single_notebook(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.ClearSolutions.code_stub=dict(python="# YOUR CODE HERE")""")

        self._copy_file(
            join("files", "test-hidden-tests.ipynb"),
            join(course_dir, "source", "ps1", "p1.ipynb")
        )
        # test-hidden-tests.ipynb contains vizable solutions that pass
        # vizable tests, but fail on hidden tests

        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        # make sure hidden tests are removed in release
        with io.open(join(course_dir, "release", "ps1", "p1.ipynb"), mode='r', encoding='utf-8') as nb:
            source = nb.read()
        assert "BEGIN HIDDEN TESTS" not in source

        self._copy_file(
            join(course_dir, "release", "ps1", "p1.ipynb"),
            join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        )

        # make sure submitted validates, should only fail on hidden tests
        output = run_nbgrader([
            "validate", join(course_dir, "submitted", "foo", "ps1", "p1.ipynb")
        ], stdout=True)
        assert output.strip() == "Success! Your notebook passes all the tests."

        run_nbgrader(["autograde", "ps1", "--db", db])
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        # make sure hidden tests are placed back in autograded
        sub_nb = join(course_dir, "autograded", "foo", "ps1", "p1.ipynb")
        with io.open(sub_nb, mode='r', encoding='utf-8') as nb:
            source = nb.read()
        assert "BEGIN HIDDEN TESTS" in source

        # make sure autograded does not validate, should fail on hidden tests
        output = run_nbgrader([
            "validate", join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"),
        ], stdout=True)
        assert output.splitlines()[0] == (
            "VALIDATION FAILED ON 2 CELL(S)! If you submit your assignment "
            "as it is, you WILL NOT"
        )

        with Gradebook(db) as gb:
            submission = gb.find_submission("ps1", "foo")
            nb1 = submission.notebooks[0]
            assert nb1.score == 1.5

    def test_handle_failure(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p2.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1"], retcode=1)

        assert not os.path.exists(join(course_dir, "autograded", "bar", "ps1"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))

    def test_handle_failure_single_notebook(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_nbgrader(["autograde", "ps1", "--notebook", "p*"], retcode=1)

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

    def test_missing_source_kernelspec(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.ClearSolutions.code_stub = {'python': '## Answer', 'blah': '## Answer'}""")

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"), kernel="python")
        run_nbgrader(["autograde", "ps1"])
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        self._empty_notebook(join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"), kernel="blarg")
        run_nbgrader(["autograde", "ps1"], retcode=1)
        assert not os.path.exists(join(course_dir, "autograded", "bar", "ps1"))

    def test_incorrect_source_kernelspec(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.ClearSolutions.code_stub = {'python': '## Answer', 'blah': '## Answer'}""")

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"), kernel="blah")
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"), kernel="python")
        run_nbgrader(["autograde", "ps1"], retcode=1)
        assert not os.path.exists(join(course_dir, "autograded", "foo", "ps1"))

    def test_incorrect_submitted_kernelspec(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"), kernel="python")
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"), kernel="blah")
        run_nbgrader(["autograde", "ps1"])
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

    def test_no_execute(self, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo"])
        run_nbgrader(["db", "student", "add", "bar"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._copy_file(join("files", "test-with-output.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        with io.open(join(os.path.dirname(__file__), "files", "test-with-output.ipynb"), mode="r", encoding='utf-8') as fh:
            orig_contents = reads(fh.read(), as_version=current_nbformat)

        run_nbgrader(["autograde", "ps1"])
        with io.open(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"), mode="r", encoding="utf-8") as fh:
            new_contents = reads(fh.read(), as_version=current_nbformat)

        different = False
        for i in range(len(orig_contents.cells)):
            orig_cell = orig_contents.cells[i]
            new_cell = new_contents.cells[i]
            if 'outputs' in orig_cell:
                if orig_cell.outputs != new_cell.outputs:
                    different = True
                    break
            elif 'outputs' in new_cell:
                different = True

        assert different

        run_nbgrader(["autograde", "ps1", "--force", "--no-execute"])
        with io.open(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"), mode="r", encoding="utf-8") as fh:
            new_contents = reads(fh.read(), as_version=current_nbformat)

        for i in range(len(orig_contents.cells)):
            orig_cell = orig_contents.cells[i]
            new_cell = new_contents.cells[i]
            if 'outputs' in orig_cell:
                assert orig_cell.outputs == new_cell.outputs
            else:
                assert 'outputs' not in new_cell

    def test_many_students(self, course_dir):
        pytest.skip("this test takes too long to run and requires manual configuration")

        # NOTE: to test this, you will manually have to configure the postgres
        # database. In the postgresql.conf file in the postgres data directory,
        # set max_connections to something low (like 5). Then, create the gradebook
        # database and run this test.
        db = "postgresql://localhost:5432/gradebook"

        run_nbgrader(["db", "assignment", "add", "ps1", "--duedate", "--db", db,
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        student_fmt = "student{:03d}"
        num_students = 50
        for i in range(num_students):
            run_nbgrader(["db", "student", "add", student_fmt.format(i), "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        for i in range(num_students):
            self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", student_fmt.format(i), "ps1", "p1.ipynb"))

        run_nbgrader(["autograde", "ps1", "--db", db])

    def test_infinite_loop(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.Execute.timeout = 1""")

        self._copy_file(join("files", "infinite-loop.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "infinite-loop.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

    def test_infinite_loop_with_output(self, db, course_dir):
        pytest.skip("this test takes too long to run and consumes a LOT of memory")

        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "infinite-loop-with-output.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "infinite-loop-with-output.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

    def test_missing_files(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        os.makedirs(join(course_dir, "submitted", "bar", "ps1"))
        run_nbgrader(["autograde", "ps1"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.exists(join(course_dir, "autograded", "bar"))

    def test_grade_missing_notebook(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

        with Gradebook(db) as gb:
            submission = gb.find_submission("ps1", "foo")
            nb1, nb2 = submission.notebooks
            assert not nb2.needs_manual_grade
            assert nb2.score == 0

    def test_grade_with_validating_envvar(self, db, course_dir):
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db, "--duedate",
                      "2015-02-02 14:58:23.948203 America/Los_Angeles"])
        run_nbgrader(["db", "student", "add", "foo", "--db", db])

        self._copy_file(join("files", "validating-environment-variable.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["generate_assignment", "ps1", "--db", db])

        self._copy_file(join("files", "validating-environment-variable.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        with Gradebook(db) as gb:
            submission = gb.find_submission("ps1", "foo")
            nb1, = submission.notebooks
            assert nb1.score == 0
