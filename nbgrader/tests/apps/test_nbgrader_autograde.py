import os
from nbgrader.api import Gradebook
from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderAutograde(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader autograde --help-all")

    def test_missing_student(self, gradebook):
        """Is an error thrown when the student is missing?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-changed.ipynb", "submitted/baz/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}" '.format(gradebook), retcode=1)

    def test_add_missing_student(self, gradebook):
        """Can a missing student be added?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-changed.ipynb", "submitted/baz/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}" --create'.format(gradebook))

        assert os.path.isfile("autograded/baz/ps1/p1.ipynb")

    def test_missing_assignment(self, gradebook):
        """Is an error thrown when the assignment is missing?"""
        self._copy_file("files/submitted-changed.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-changed.ipynb", "submitted/ps2/foo/p1.ipynb")
        run_command('nbgrader autograde ps2 --db="{}" '.format(gradebook), retcode=1)

    def test_grade(self, gradebook):
        """Can files be graded?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._copy_file("files/submitted-changed.ipynb", "submitted/bar/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/bar/ps1/timestamp.txt")

        gb = Gradebook(gradebook)
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

    def test_grade_timestamp(self, gradebook):
        """Is a timestamp correctly read in?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")

        self._copy_file("files/submitted-changed.ipynb", "submitted/bar/ps1/p1.ipynb")
        self._make_file('submitted/bar/ps1/timestamp.txt', "2015-02-01 14:58:23.948203 PST")

        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/bar/ps1/p1.ipynb")
        assert os.path.isfile("autograded/bar/ps1/timestamp.txt")

        gb = Gradebook(gradebook)
        submission = gb.find_submission('ps1', 'foo')
        assert submission.total_seconds_late > 0
        submission = gb.find_submission('ps1', 'bar')
        assert submission.total_seconds_late == 0

        # make sure it still works to run it a second time
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

    def test_force(self, gradebook):
        """Ensure the force option works properly"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that it skips the existing directory
        os.chmod("autograded/foo/ps1/foo.txt", 0o666)
        os.remove("autograded/foo/ps1/foo.txt")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")

        # force overwrite the supplemental files
        run_command('nbgrader autograde ps1 --db="{}" --force'.format(gradebook))
        assert os.path.isfile("autograded/foo/ps1/foo.txt")

        # force overwrite
        os.chmod("source/ps1/foo.txt", 0o666)
        os.remove("source/ps1/foo.txt")
        os.chmod("submitted/foo/ps1/foo.txt", 0o666)
        os.remove("submitted/foo/ps1/foo.txt")
        run_command('nbgrader autograde ps1 --db="{}" --force'.format(gradebook))
        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

    def test_filter_notebook(self, gradebook):
        """Does autograding filter by notebook properly?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/foo.txt", "foo")
        self._make_file("source/ps1/data/bar.txt", "bar")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file("submitted/foo/ps1/foo.txt", "foo")
        self._make_file("submitted/foo/ps1/data/bar.txt", "bar")
        self._make_file("submitted/foo/ps1/blah.pyc", "asdf")
        run_command('nbgrader autograde ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that removing the notebook still causes the autograder to run
        os.chmod("autograded/foo/ps1/p1.ipynb", 0o666)
        os.remove("autograded/foo/ps1/p1.ipynb")
        os.chmod("autograded/foo/ps1/foo.txt", 0o666)
        os.remove("autograded/foo/ps1/foo.txt")
        run_command('nbgrader autograde ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that running it again doesn't do anything
        os.chmod("autograded/foo/ps1/foo.txt", 0o666)
        os.remove("autograded/foo/ps1/foo.txt")
        run_command('nbgrader autograde ps1 --db="{}" --notebook "p1"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

        # check that removing the notebook doesn't caus the autograder to run
        os.chmod("autograded/foo/ps1/p1.ipynb", 0o666)
        os.remove("autograded/foo/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert not os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/foo.txt")
        assert os.path.isfile("autograded/foo/ps1/data/bar.txt")
        assert not os.path.isfile("autograded/foo/ps1/blah.pyc")

    def test_grade_overwrite_files(self, gradebook):
        """Are dependent files properly linked and overwritten?"""
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        self._make_file("source/ps1/data.csv", "some,data\n")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1.ipynb")
        self._make_file('submitted/foo/ps1/timestamp.txt', "2015-02-02 15:58:23.948203 PST")
        self._make_file("submitted/foo/ps1/data.csv", "some,other,data\n")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert os.path.isfile("autograded/foo/ps1/timestamp.txt")
        assert os.path.isfile("autograded/foo/ps1/data.csv")

        with open("autograded/foo/ps1/timestamp.txt", "r") as fh:
            contents = fh.read()
        assert contents == "2015-02-02 15:58:23.948203 PST"

        with open("autograded/foo/ps1/data.csv", "r") as fh:
            contents = fh.read()
        assert contents == "some,data\n"

    def test_side_effects(self, gradebook):
        self._copy_file("files/side-effects.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/side-effects.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/side-effect.txt")
        assert not os.path.isfile("submitted/foo/ps1/side-effect.txt")

    def test_skip_extra_notebooks(self, gradebook):
        self._copy_file("files/submitted-unchanged.ipynb", "source/ps1/p1.ipynb")
        run_command('nbgrader assign ps1 --db="{}" '.format(gradebook))

        self._copy_file("files/submitted-unchanged.ipynb", "submitted/foo/ps1/p1 copy.ipynb")
        self._copy_file("files/submitted-changed.ipynb", "submitted/foo/ps1/p1.ipynb")
        run_command('nbgrader autograde ps1 --db="{}"'.format(gradebook))

        assert os.path.isfile("autograded/foo/ps1/p1.ipynb")
        assert not os.path.isfile("autograded/foo/ps1/p1 copy.ipynb")

    def test_permissions(self):
        """Are permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_command("nbgrader assign ps1 --create")

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        self._make_file("source/foo/ps1/foo.txt", "foo")
        run_command("nbgrader autograde ps1 --create")

        assert os.path.isfile("autograded/foo/ps1/foo.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert self._get_permissions("autograded/foo/ps1/foo.ipynb") == "444"
        assert self._get_permissions("autograded/foo/ps1/foo.txt") == "444"

    def test_custom_permissions(self):
        """Are custom permissions properly set?"""
        self._empty_notebook('source/ps1/foo.ipynb')
        self._make_file("source/ps1/foo.txt", "foo")
        run_command("nbgrader assign ps1 --create")

        self._empty_notebook('submitted/foo/ps1/foo.ipynb')
        self._make_file("source/foo/ps1/foo.txt", "foo")
        run_command("nbgrader autograde ps1 --create --AutogradeApp.permissions=666")

        assert os.path.isfile("autograded/foo/ps1/foo.ipynb")
        assert os.path.isfile("autograded/foo/ps1/foo.txt")
        assert self._get_permissions("autograded/foo/ps1/foo.ipynb") == "666"
        assert self._get_permissions("autograded/foo/ps1/foo.txt") == "666"
