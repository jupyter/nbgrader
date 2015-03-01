from .base import TestBase

import os

class TestNbgraderAssign(TestBase):

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader assign --help-all")

    def test_single_file(self):
        """Can a single file be assigned?"""
        with self._temp_cwd():
            self._empty_notebook('teacher.ipynb')
            self._run_command("nbgrader assign teacher.ipynb")
            assert os.path.isfile("teacher.nbconvert.ipynb")

    def test_single_file_output(self):
        """Can a single file be assigned to a different filename?"""
        with self._temp_cwd():
            self._empty_notebook('teacher.ipynb')
            self._run_command("nbgrader assign teacher.ipynb --output=student.ipynb")
            assert os.path.isfile("student.ipynb")

    def test_build_directory(self):
        """Is the notebook properly saved to the build directory?"""
        with self._temp_cwd():
            self._empty_notebook("Problem 1.ipynb")
            self._empty_notebook("Problem 2.ipynb")
            self._run_command('nbgrader assign *.ipynb --build-dir=student')
            assert os.path.isdir('student')
            assert os.path.isfile('student/Problem 1.ipynb')
            assert os.path.isfile('student/Problem 2.ipynb')

    def test_source_and_build_directory(self):
        """Is the notebook properly saved to the build directory from a source directory?"""
        with self._temp_cwd():
            os.mkdir('teacher')
            self._empty_notebook("teacher/Problem 1.ipynb")
            self._empty_notebook("teacher/Problem 2.ipynb")
            self._run_command('nbgrader assign teacher/*.ipynb --build-dir=student')
            assert os.path.isdir('student')
            assert os.path.isfile('student/Problem 1.ipynb')
            assert os.path.isfile('student/Problem 2.ipynb')

    def test_dependent_files(self):
        """Are dependent files properly linked?"""
        with self._temp_cwd():
            os.mkdir('teacher')
            self._empty_notebook("teacher/Problem 1.ipynb")
            self._empty_notebook("teacher/Problem 2.ipynb")

            # add some fake dependencies
            os.mkdir('teacher/data')
            with open('teacher/data/foo.csv', 'w') as fh:
                fh.write('foo')
            with open('teacher/data/bar.csv', 'w') as fh:
                fh.write('bar')

            self._run_command(
                'nbgrader assign teacher/*.ipynb '
                '--build-dir=student '
                '--files=\'["teacher/data/*.csv"]\' '
                '--relpath=teacher'
            )

            assert os.path.isdir('student')
            assert os.path.isfile('student/Problem 1.ipynb')
            assert os.path.isfile('student/Problem 2.ipynb')
            assert os.path.isdir('student/data')
            assert os.path.isfile('student/data/foo.csv')
            assert os.path.isfile('student/data/bar.csv')

            with open('student/data/foo.csv', 'r') as fh:
                assert fh.read() == 'foo'
            with open('student/data/bar.csv', 'r') as fh:
                assert fh.read() == 'bar'
