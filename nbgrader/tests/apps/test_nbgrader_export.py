import os
import sys

from os.path import join
from textwrap import dedent
from nbformat.v4 import reads

from ...api import Gradebook
from ...utils import remove
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderExport(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["export", "--help-all"])

    def test_export(self, db, course_dir):
        """Is an error thrown when the student is missing?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "baz", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

        run_nbgrader(["export", "--db", db])
        assert os.path.isfile("grades.csv")

        run_nbgrader(["export", "--db", db, "--to", "mygrades.csv"])
        assert os.path.isfile("mygrades.csv")

        run_nbgrader(["export", "--db", db, "--exporter", "nbgrader.plugins.CsvExportPlugin"])
        assert os.path.isfile("grades.csv")
