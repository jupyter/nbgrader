import os
import time
import pytest

from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows
from ...utils import parse_utc, get_username


@notwindows
class TestNbGraderCollect(BaseTestApp):

    def _release_and_fetch(self, assignment, exchange, course_dir):
        self._copy_file(os.path.join("files", "test.ipynb"), os.path.join(course_dir, "release", "ps1", "p1.ipynb"))
        run_nbgrader([
            "release_assignment", assignment,
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ])
        run_nbgrader([
            "fetch_assignment", assignment,
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ])

    def _submit(self, assignment, exchange, cache, flags=None):
        cmd = [
            "submit", assignment,
            "--course", "abc101",
            "--Exchange.cache={}".format(cache),
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)
        run_nbgrader(cmd)

    def _collect(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "collect", assignment,
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        return run_nbgrader(cmd, retcode=retcode)

    def _read_timestamp(self, root):
        with open(os.path.os.path.join(root, "timestamp.txt"), "r") as fh:
            timestamp = parse_utc(fh.read())
        return timestamp

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["collect", "--help-all"])

    def test_no_course_id(self, exchange, course_dir, cache):
        """Does releasing without a course id thrown an error?"""
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange, cache)
        cmd = [
            "collect", "ps1",
            "--Exchange.root={}".format(exchange)
        ]
        run_nbgrader(cmd, retcode=1)

    def test_collect(self, exchange, course_dir, cache):
        self._release_and_fetch("ps1", exchange, course_dir)

        # try to collect when there"s nothing to collect
        self._collect("ps1", exchange)
        root = os.path.os.path.join(os.path.join(course_dir, "submitted", get_username(), "ps1"))
        assert not os.path.isdir(os.path.join(course_dir, "submitted"))

        # submit something
        self._submit("ps1", exchange, cache)
        time.sleep(1)

        # try to collect it
        self._collect("ps1", exchange)
        assert os.path.isfile(os.path.os.path.join(root, "p1.ipynb"))
        assert os.path.isfile(os.path.os.path.join(root, "timestamp.txt"))
        timestamp = self._read_timestamp(root)

        # try to collect it again
        self._collect("ps1", exchange)
        assert self._read_timestamp(root) == timestamp

        # submit again
        self._submit("ps1", exchange, cache)

        # collect again
        self._collect("ps1", exchange)
        assert self._read_timestamp(root) == timestamp

        # collect again with --update
        self._collect("ps1", exchange, ["--update"])
        assert self._read_timestamp(root) != timestamp

    def test_collect_assignment_flag(self, exchange, course_dir, cache):
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange, cache)

        # try to collect when there"s nothing to collect
        self._collect("--assignment=ps1", exchange)
        root = os.path.os.path.join(os.path.join(course_dir, "submitted", get_username(), "ps1"))
        assert os.path.isfile(os.path.os.path.join(root, "p1.ipynb"))
        assert os.path.isfile(os.path.os.path.join(root, "timestamp.txt"))

    def test_collect_subdirectories(self, exchange, course_dir, cache):
        self._release_and_fetch("ps1", exchange, course_dir)

        # create a subdirectory with an empty file
        os.makedirs(os.path.join('ps1', 'foo'))
        with open(os.path.join('ps1', 'foo', 'temp.txt'), 'w') as fh:
            fh.write("")

        self._submit("ps1", exchange, cache)

        # make sure collect succeeds
        self._collect("ps1", exchange)

    def test_owner_check(self, exchange, course_dir, cache):
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange, cache, flags=["--student=foobar_student",])

        # By default, a warning is raised if the student id does not match the directory owner
        out = self._collect("--assignment=ps1", exchange)
        assert 'WARNING' in out

        # This warning can be disabled
        out = self._collect("--assignment=ps1", exchange, flags=["--ExchangeCollect.check_owner=False"])
        assert 'WARNING' not in out

    @notwindows
    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, exchange, course_dir, cache, groupshared):
        if groupshared:
            with open("nbgrader_config.py", "a") as fh:
                fh.write("""c.CourseDirectory.groupshared = True\n""")
        self._release_and_fetch("ps1", exchange, course_dir)
        self._submit("ps1", exchange, cache, flags=["--student=foobar_student",])

        # By default, a warning is raised if the student id does not match the directory owner
        self._collect("--assignment=ps1", exchange)
        assert self._get_permissions(join(exchange, "abc101", "inbound")) == ("2733" if not groupshared else "2773")
        assert self._get_permissions(join(course_dir, "submitted", "foobar_student", "ps1")) == ("777" if not groupshared else "2777")
        assert self._get_permissions(join(course_dir, "submitted", "foobar_student", "ps1", "p1.ipynb")) == ("644" if not groupshared else "664")
