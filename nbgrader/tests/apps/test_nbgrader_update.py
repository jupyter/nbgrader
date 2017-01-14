from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderUpdate(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["update", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_nbgrader(["update"], retcode=1)

    def test_update(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test-v0.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db], retcode=1)

        # now update the metadata
        run_nbgrader(["update", course_dir])

        # now assign should suceed
        run_nbgrader(["assign", "ps1", "--db", db])

        # autograde should fail on old metadata, too
        self._copy_file(join("files", "test-v0.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

        # now update the metadata
        run_nbgrader(["update", course_dir])

        # now autograde should suceed
        run_nbgrader(["autograde", "ps1", "--db", db])
