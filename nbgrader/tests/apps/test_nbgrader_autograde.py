import os
import sys

from os.path import join

from ...api import Gradebook
from ...utils import remove
from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderAutograde(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "autograde", "--help-all"])

    def test_missing_student(self, db, course_dir):
        """Is an error thrown when the student is missing?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "baz", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db], retcode=1)

        # check that --create is properly deprecated
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--create"], retcode=1)

    def test_missing_assignment(self, db, course_dir):
        """Is an error thrown when the assignment is missing?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "ps2", "foo", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps2", "--db", db], retcode=1)

    def test_grade(self, db, course_dir):
        """Can files be graded?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        gb = Gradebook(db)
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

        gb.db.close()

    def test_grade_timestamp(self, db, course_dir):
        """Is a timestamp correctly read in?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "bar", "ps1", "timestamp.txt"), "2015-02-01 14:58:23.948203 PST")

        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "bar", "ps1", "timestamp.txt"))

        gb = Gradebook(db)
        submission = gb.find_submission("ps1", "foo")
        assert submission.total_seconds_late > 0
        submission = gb.find_submission("ps1", "bar")
        assert submission.total_seconds_late == 0

        # make sure it still works to run it a second time
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        gb.db.close()

    def test_force(self, db, course_dir):
        """Ensure the force option works properly"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--force"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))

        # force overwrite
        remove(join(course_dir, "source", "ps1", "foo.txt"))
        remove(join(course_dir, "submitted", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--force"])
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

    def test_filter_notebook(self, db, course_dir):
        """Does autograding filter by notebook properly?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook still causes the autograder to run
        remove(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that running it again doesn"t do anything
        remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db, "--notebook", "p1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook doesn"t caus the autograder to run
        remove(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"))

    def test_grade_overwrite_files(self, db, course_dir):
        """Are dependent files properly linked and overwritten?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "data.csv"), "some,data\n")
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data.csv"), "some,other,data\n")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "data.csv"))

        with open(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "r") as fh:
            contents = fh.read()
        assert contents == "2015-02-02 15:58:23.948203 PST"

        with open(join(course_dir, "autograded", "foo", "ps1", "data.csv"), "r") as fh:
            contents = fh.read()
        assert contents == "some,data\n"

    def test_side_effects(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "side-effects.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "side-effects.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "side-effect.txt"))
        assert not os.path.isfile(join(course_dir, "submitted", "foo", "ps1", "side-effect.txt"))

    def test_skip_extra_notebooks(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1 copy.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", db])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1 copy.ipynb"))

    def test_permissions(self, course_dir):
        """Are permissions properly set?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        run_python_module(["nbgrader", "assign", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "foo", "ps1", "foo.txt"), "foo")
        run_python_module(["nbgrader", "autograde", "ps1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb")) == "444"
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.txt")) == "444"

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        run_python_module(["nbgrader", "assign", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        self._make_file(join(course_dir, "source", "foo", "ps1", "foo.txt"), "foo")
        run_python_module(["nbgrader", "autograde", "ps1", "--AutogradeApp.permissions=644"])

        if sys.platform == 'win32':
            perms = '666'
        else:
            perms = '644'

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.ipynb")) == perms
        assert self._get_permissions(join(course_dir, "autograded", "foo", "ps1", "foo.txt")) == perms

    def test_force_single_notebook(self, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        p1 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

    def test_update_newer(self, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 PST"
        p = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1"])

        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 PST"
        assert p != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

    def test_update_newer_single_notebook(self, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 PST"
        p1 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--notebook", "p1"])

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        assert os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 PST"
        assert p1 != self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))

    def test_handle_failure(self, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1"], retcode=1)

        assert not os.path.exists(join(course_dir, "autograded", "foo", "ps1"))

    def test_handle_failure_single_notebook(self, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._empty_notebook(join(course_dir, "source", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--notebook", "p*"], retcode=1)

        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        assert not os.path.isfile(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
