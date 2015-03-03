import os
import shutil
import tarfile

from nose.tools import assert_equal
from .base import TestBase

class TestNbgraderSubmit(TestBase):

    def test_help(self):
        """Does the help display properly?"""
        self._run_command(["nbgrader", "submit", "--help-all"])

    def test_submit(self):
        """Does everything get properly submitted?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            os.mkdir('Problem Set 1')
            shutil.move('submitted.ipynb', 'Problem Set 1/Problem 1.ipynb')
            os.chdir('Problem Set 1')
            self._run_command('nbgrader submit --log-level=DEBUG --submit-dir=..')
            assert os.path.isfile("../Problem Set 1.tar.gz")

            tf = tarfile.open('../Problem Set 1.tar.gz', 'r:gz')
            names = ['Problem Set 1/Problem 1.ipynb', 'Problem Set 1/timestamp.txt', 'Problem Set 1/user.txt']
            assert_equal(tf.getnames(), names, "incorrect tarfile names")

    def test_submit_custom_assignment(self):
        """Does everything get properly submitted with a custom assignment name?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            os.mkdir('Problem Set 1')
            shutil.move('submitted.ipynb', 'Problem Set 1/Problem 1.ipynb')
            os.chdir('Problem Set 1')
            self._run_command('nbgrader submit --log-level=DEBUG --submit-dir=.. --assignment=foo')
            assert os.path.isfile("../foo.tar.gz")

            tf = tarfile.open('../foo.tar.gz', 'r:gz')
            names = ['foo/Problem 1.ipynb', 'foo/timestamp.txt', 'foo/user.txt']
            assert_equal(tf.getnames(), names, "incorrect tarfile names")
