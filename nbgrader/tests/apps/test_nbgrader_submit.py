import os
import tarfile

from nbgrader.tests import run_command
from nbgrader.tests.apps.base import BaseTestApp


class TestNbGraderSubmit(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_command("nbgrader submit --help-all")


    def test_submit(self):
        """Does everything get properly submitted?"""
        pass # TODO: fix these for the new submit command
        # with temp_cwd([os.path.join(root, "files/submitted-changed.ipynb")]):
        #     os.mkdir('Problem Set 1')
        #     shutil.move('submitted-changed.ipynb', 'Problem Set 1/Problem 1.ipynb')
        #     os.chdir('Problem Set 1')
        #     run_command('nbgrader submit --log-level=DEBUG --submit-dir=..')
        #     assert os.path.isfile("../Problem Set 1.tar.gz")

        #     tf = tarfile.open('../Problem Set 1.tar.gz', 'r:gz')
        #     names = sorted(['Problem Set 1/Problem 1.ipynb', 'Problem Set 1/timestamp.txt', 'Problem Set 1/user.txt'])
        #     assert sorted(tf.getnames()) == names


    def test_submit_custom_assignment(self):
        """Does everything get properly submitted with a custom assignment name?"""
        pass # TODO: fix these for the new submit command
        # with temp_cwd([os.path.join(root, "files/submitted-changed.ipynb")]):
        #     os.mkdir('Problem Set 1')
        #     shutil.move('submitted-changed.ipynb', 'Problem Set 1/Problem 1.ipynb')
        #     os.chdir('Problem Set 1')
        #     run_command('nbgrader submit --log-level=DEBUG --submit-dir=.. --assignment=foo')
        #     assert os.path.isfile("../foo.tar.gz")

        #     tf = tarfile.open('../foo.tar.gz', 'r:gz')
        #     names = sorted(['foo/Problem 1.ipynb', 'foo/timestamp.txt', 'foo/user.txt'])
        #     assert sorted(tf.getnames()) == names
