import os
import sys
import pytest

from os.path import join
from sqlalchemy.exc import InvalidRequestError
from textwrap import dedent

from ...api import Gradebook
from .. import run_nbgrader
from .base import BaseTestApp
from tempfile import TemporaryDirectory


class TestNbGraderAssign(BaseTestApp):

    def test_removehidden(self, db, course_dir):
        """Test whether hidden tests are removed from the released version
        and later on reinstantiated correctly."""


        # need to put the exchange directory elsewhere
        # TODO: understand how to access the TransferApp settings, like in the collect test?
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.TransferApp.exchange_directory = '/Users/hkarl/tmp/nbgrader'\n""")

        # need to put the assignment into the config file:
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name="ps1")]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="hkarl"), ]""")


        # copy the test input file into place and read it in for later comparison
        self._copy_file(join('files', 'hidden-tests.ipynb'), join(course_dir, 'source', 'ps1', 'test.ipynb'))
        with open(join(course_dir, 'source', 'ps1', 'test.ipynb')) as fh:
            orig_nb = fh.read()

        # assign this file:
        run_nbgrader(["assign", "ps1", "--db", db])

        # Check that there are no hidden tests contained any more in the released notebook
        with open(join(course_dir, 'release', 'ps1', 'test.ipynb')) as fh:
            released_nb = fh.read()
            # print (released_nb)

        assert "HIDESTART" not in released_nb
        assert "HIDEEND" not in released_nb

        # Release it
        run_nbgrader([
            "release", "ps1",
            "--course", "abc101",
            "--force",
        ])

        # Have this new notebook fetched
        run_nbgrader(["fetch", "ps1", "--db", db,
                      "--course", "abc101",
                      ])

        # Have this notebook submitted
        run_nbgrader(["submit", "ps1", "--db", db,
                      "--course", "abc101",
                      ])

        # Collect the submitted notebook
        run_nbgrader(["collect", "ps1", "--db", db,
                      "--course", "abc101",
                      ])

        run_nbgrader(["autograde", "ps1", "--db", db,
                      "--course", "abc101",
                      ])

        # Check that the submitted & collected notebook has the original tests reintroduced
        with open(join(course_dir, 'autograded', 'hkarl', 'ps1', 'test.ipynb')) as fh:
            autograded_nb = fh.read()

        assert "HIDESTART" in autograded_nb
        assert "HIDEEND"  in autograded_nb
    #----------------------------
