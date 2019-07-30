import os
import shutil
import stat
import pytest
from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows


@notwindows
class TestNbGraderRelease(BaseTestApp):

    def _release(self, assignment, exchange, flags=None, retcode=0):
        cmd = [
            "release_assignment", assignment,
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_nbgrader(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["release_assignment", "--help-all"])

    def test_no_course_id(self, exchange):
        """Does releasing without a course id thrown an error?"""
        cmd = [
            "release_assignment", "ps1",
            "--Exchange.root={}".format(exchange)
        ]
        run_nbgrader(cmd, retcode=1)

    def test_release(self, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_release_deprecated(self, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        run_nbgrader([
            "release_assignment", "ps1",
            "--course", "abc101",
            "--Exchange.root={}".format(exchange)
        ])
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_force_release(self, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

        self._release("ps1", exchange, retcode=1)

        os.remove(join(exchange, join("abc101", "outbound", "ps1", "p1.ipynb")))
        self._release("ps1", exchange, retcode=1)

        self._release("ps1", exchange, flags=["--force"])
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_force_release_f(self, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

        self._release("ps1", exchange, retcode=1)

        os.remove(join(exchange, join("abc101", "outbound", "ps1", "p1.ipynb")))
        self._release("ps1", exchange, retcode=1)

        self._release("ps1", exchange, flags=["-f"])
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_release_with_assignment_flag(self, exchange, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("--assignment=ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_no_exchange(self, exchange, course_dir):
        shutil.rmtree(exchange)
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("--assignment=ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    def test_exchange_bad_perms(self, exchange, course_dir):
        perms = stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP
        os.chmod(exchange, perms)
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("--assignment=ps1", exchange)
        assert os.path.isfile(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    @notwindows
    @pytest.mark.parametrize("groupshared", [False, True])
    def test_permissions(self, exchange, course_dir, groupshared):
        if groupshared:
            with open("nbgrader_config.py", "a") as fh:
                fh.write("""c.CourseDirectory.groupshared = True""")
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        self._release("--assignment=ps1", exchange)
        assert self._get_permissions(join(exchange, "abc101", "outbound", "ps1")) == ("755" if not groupshared else "2775")
        assert self._get_permissions(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb")) == ("644" if not groupshared else "664")
