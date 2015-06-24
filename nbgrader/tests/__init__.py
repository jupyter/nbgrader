import os
import glob
import shutil
import subprocess as sp

from IPython.nbformat.v4 import new_code_cell, new_markdown_cell

from nbgrader.utils import compute_checksum


def create_code_cell():
    source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
    cell = new_code_cell(source=source)
    return cell


def create_text_cell():
    source = "this is the answer!\n"
    cell = new_markdown_cell(source=source)
    return cell


def create_grade_cell(source, cell_type, grade_id, points):
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

    return cell


def create_solution_cell(source, cell_type, grade_id):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["solution"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id

    return cell


def create_locked_cell(source, cell_type, grade_id):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["locked"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id

    return cell


def create_grade_and_solution_cell(source, cell_type, grade_id, points):
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

    return cell


def start_subprocess(command, **kwargs):
    kwargs['env'] = kwargs.get('env', os.environ.copy())
    proc = sp.Popen(command, **kwargs)
    return proc


def copy_coverage_files():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if os.getcwd() != root:
        coverage_files = glob.glob(".coverage.*")
        if len(coverage_files) == 0 and 'COVERAGE_PROCESS_START' in os.environ:
            raise RuntimeError("No coverage files produced")
        for filename in coverage_files:
            shutil.copyfile(filename, os.path.join(root, filename))


def run_command(command, retcode=0):
    proc = start_subprocess(command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
    true_retcode = proc.wait()
    output = proc.communicate()[0].decode()
    output = output.replace("Coverage.py warning: No data was collected.\n", "")
    if true_retcode != retcode:
        print(output)
        raise AssertionError(
            "process returned an unexpected return code: {}".format(true_retcode))
    copy_coverage_files()
    return output
