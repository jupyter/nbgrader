import os
import glob
import shutil
import subprocess as sp

from IPython.utils.tempdir import TemporaryWorkingDirectory
from IPython.nbformat import current_nbformat
from IPython.nbformat import read as read_nb
from IPython.nbformat import write as write_nb
from IPython.nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from nbgrader.utils import compute_checksum


class TestBase(object):

    pth = os.path.split(os.path.realpath(__file__))[0]
    files = {os.path.basename(x): x for x in glob.glob(os.path.join(pth, "files/*.ipynb"))}

    def setup(self):
        self.nbs = {}
        for basename, filename in self.files.items():
            with open(filename, "r") as fh:
                self.nbs[basename] = read_nb(fh, as_version=current_nbformat)

    @staticmethod
    def _create_code_cell():
        source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
        cell = new_code_cell(source=source)
        return cell

    @staticmethod
    def _create_text_cell():
        source = "this is the answer!\n"
        cell = new_markdown_cell(source=source)
        return cell

    @staticmethod
    def _create_grade_cell(source, cell_type, grade_id, points):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["grade"] = True
        cell.metadata.nbgrader["grade_id"] = grade_id
        cell.metadata.nbgrader["points"] = points
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell

    @staticmethod
    def _create_solution_cell(source, cell_type):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["solution"] = True
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell

    @staticmethod
    def _create_grade_and_solution_cell(source, cell_type, grade_id, points):
        if cell_type == "markdown":
            cell = new_markdown_cell(source=source)
        elif cell_type == "code":
            cell = new_code_cell(source=source)
        else:
            raise ValueError("invalid cell type: {}".format(cell_type))

        cell.metadata.nbgrader = {}
        cell.metadata.nbgrader["solution"] = True
        cell.metadata.nbgrader["grade"] = True
        cell.metadata.nbgrader["grade_id"] = grade_id
        cell.metadata.nbgrader["points"] = points
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)

        return cell


    @staticmethod
    def _empty_notebook(path):
        nb = new_notebook()
        with open(path, 'w') as f:
            write_nb(nb, f, 4)    

    @staticmethod
    def _temp_cwd(copy_filenames=None):
        temp_dir = TemporaryWorkingDirectory()

        if copy_filenames is not None:
            files_path = os.path.dirname(__file__)
            for pattern in copy_filenames:
                for match in glob.glob(os.path.join(files_path, pattern)):
                    dest = os.path.join(temp_dir.name, os.path.basename(match))
                    shutil.copyfile(match, dest)

        return temp_dir

    @classmethod
    def _start_subprocess(cls, command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT, cwd=None):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env = os.environ.copy()
        env['COVERAGE_PROCESS_START'] = os.path.join(root, ".coveragerc")
        proc = sp.Popen(command, shell=shell, stdout=stdout, stderr=stderr, env=env, cwd=cwd)
        return proc

    @classmethod
    def _copy_coverage_files(cls):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))        
        if os.getcwd() != root:
            coverage_files = glob.glob(".coverage.*")
            if len(coverage_files) == 0:
                raise RuntimeError("No coverage files produced")
            for filename in coverage_files:
                shutil.copyfile(filename, os.path.join(root, filename))

    @classmethod
    def _run_command(cls, command, retcode=0):
        proc = cls._start_subprocess(command)
        true_retcode = proc.wait()
        output = proc.communicate()[0].decode()
        if true_retcode != retcode:
            print(output)
            raise AssertionError(
                "process returned an unexpected return code: {}".format(true_retcode))
        cls._copy_coverage_files()
        return output

    @staticmethod
    def _init_db():
        dbpath = "/tmp/nbgrader_test.db"
        if os.path.exists(dbpath):
            os.remove(dbpath)
        return "sqlite:///" + dbpath
