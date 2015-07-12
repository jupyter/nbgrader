import os
import pytest
import tempfile
import shutil

from IPython.nbformat.v4 import new_output

from nbgrader import utils
from nbgrader.tests import (
    create_code_cell,
    create_grade_cell, create_solution_cell,
    create_grade_and_solution_cell)


@pytest.fixture
def temp_cwd(request):
    orig_dir = os.getcwd()
    path = tempfile.mkdtemp()
    os.chdir(path)

    def fin():
        os.chdir(orig_dir)
        for r,d,f in os.walk(path):
            os.chmod(r, 0o666)
            for filename in f:
                os.chmod(os.path.join(r, filename), 0o666)
        shutil.rmtree(path)
    request.addfinalizer(fin)

    return path


def test_is_grade():
    cell = create_code_cell()
    assert not utils.is_grade(cell)
    cell.metadata['nbgrader'] = {}
    assert not utils.is_grade(cell)
    cell.metadata['nbgrader']['grade'] = False
    assert not utils.is_grade(cell)
    cell.metadata['nbgrader']['grade'] = True
    assert utils.is_grade(cell)


def test_is_solution():
    cell = create_code_cell()
    assert not utils.is_solution(cell)
    cell.metadata['nbgrader'] = {}
    assert not utils.is_solution(cell)
    cell.metadata['nbgrader']['solution'] = False
    assert not utils.is_solution(cell)
    cell.metadata['nbgrader']['solution'] = True
    assert utils.is_solution(cell)


def test_is_locked():

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=True, grade=False, locked=False)
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=True, grade=True, locked=False)
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=True, grade=False, locked=True)
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=True, grade=True, locked=True)
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=False, grade=True, locked=False)
    assert utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=False, grade=True, locked=True)
    assert utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=False, grade=False, locked=True)
    assert utils.is_locked(cell)

    assert utils.is_locked(cell)
    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata['nbgrader'] = dict(solution=False, grade=False, locked=False)
    assert not utils.is_locked(cell)



def test_determine_grade_code_grade():
    cell = create_grade_cell('print("test")', "code", "foo", 10)
    cell.outputs = []
    assert utils.determine_grade(cell) == (10, 10)

    cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
    assert utils.determine_grade(cell) == (0, 10)


def test_determine_grade_markdown_grade():
    cell = create_grade_cell('test', "markdown", "foo", 10)
    assert utils.determine_grade(cell) == (None, 10)


def test_determine_grade_solution():
    cell = create_solution_cell('test', "code", "foo")
    with pytest.raises(ValueError):
        utils.determine_grade(cell)

    cell = create_solution_cell('test', "markdown", "foo")
    with pytest.raises(ValueError):
        utils.determine_grade(cell)


def test_determine_grade_code_grade_and_solution():
    cell = create_grade_and_solution_cell('test', "code", "foo", 10)
    cell.metadata.nbgrader['checksum'] = utils.compute_checksum(cell)
    cell.outputs = []
    assert utils.determine_grade(cell) == (0, 10)

    cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
    cell.source = 'test!'
    assert utils.determine_grade(cell) == (None, 10)


def test_determine_grade_markdown_grade_and_solution():
    cell = create_grade_and_solution_cell('test', "markdown", "foo", 10)
    cell.metadata.nbgrader['checksum'] = utils.compute_checksum(cell)
    assert utils.determine_grade(cell) == (0, 10)

    cell = create_grade_and_solution_cell('test', "markdown", "foo", 10)
    cell.source = 'test!'
    assert utils.determine_grade(cell) == (None, 10)


def test_compute_checksum_identical():
    # is the same for two identical cells?
    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello", "code", "foo", 1)
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", "code", "foo")
    cell2 = create_solution_cell("hello", "code", "foo")
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)


def test_compute_checksum_cell_type():
    # does the cell type make a difference?
    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello", "markdown", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", "code", "foo")
    cell2 = create_solution_cell("hello", "markdown", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_whitespace():
    # does whitespace make no difference?
    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello ", "code", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", "markdown", "foo", 1)
    cell2 = create_grade_cell("hello ", "markdown", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", "code", "foo")
    cell2 = create_solution_cell("hello ", "code", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", "markdown", "foo")
    cell2 = create_solution_cell("hello ", "markdown", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_source():
    # does the source make a difference?
    cell1 = create_grade_cell("print('hello')", "code", "foo", 1)
    cell2 = create_grade_cell("print( 'hello' )", "code", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("print('hello')", "code", "foo", 1)
    cell2 = create_grade_cell("print( 'hello!' )", "code", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("print('hello')", "markdown", "foo", 1)
    cell2 = create_grade_cell("print( 'hello' )", "markdown", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", "code", "foo")
    cell2 = create_solution_cell("print( 'hello' )", "code", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", "code", "foo")
    cell2 = create_solution_cell("print( 'hello!' )", "code", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", "markdown", "foo")
    cell2 = create_solution_cell("print( 'hello' )", "markdown", "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_points():
    # does the number of points make a difference (only for grade cells)?
    cell1 = create_grade_cell("hello", "code", "foo", 2)
    cell2 = create_grade_cell("hello", "code", "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", "code", "foo", 2)
    cell2 = create_grade_cell("hello", "code", "foo", 1)
    cell1.metadata.nbgrader["grade"] = False
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)


def test_compute_checksum_grade_id():
    # does the grade id make a difference (only for grade cells)?
    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello", "code", "bar", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello", "code", "bar", 1)
    cell1.metadata.nbgrader["grade"] = False
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_grade_cell():
    # does it make a difference if grade=True?
    cell1 = create_grade_cell("hello", "code", "foo", 1)
    cell2 = create_grade_cell("hello", "code", "foo", 1)
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_solution_cell():
    # does it make a difference if solution=True?
    cell1 = create_solution_cell("hello", "code", "foo")
    cell2 = create_solution_cell("hello", "code", "foo")
    cell2.metadata.nbgrader["solution"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_is_ignored(temp_cwd):
    os.mkdir("foo")
    with open("foo/bar.txt", "w") as fh:
        fh.write("bar")

    assert not utils.is_ignored("foo")
    assert utils.is_ignored("foo/bar.txt", ["*.txt"])
    assert utils.is_ignored("foo/bar.txt", ["bar.txt"])
    assert utils.is_ignored("foo/bar.txt", ["*"])
    assert not utils.is_ignored("foo/bar.txt", ["*.csv"])
    assert not utils.is_ignored("foo/bar.txt", ["foo"])
    assert not utils.is_ignored("foo/bar.txt", ["foo/*"])


def test_find_all_files(temp_cwd):
    os.makedirs("foo/bar")
    with open("foo/baz.txt", "w") as fh:
        fh.write("baz")
    with open("foo/bar/baz.txt", "w") as fh:
        fh.write("baz")

    assert utils.find_all_files("foo") == ["foo/baz.txt", "foo/bar/baz.txt"]
    assert utils.find_all_files("foo", ["bar"]) == ["foo/baz.txt"]
    assert utils.find_all_files("foo/bar") == ["foo/bar/baz.txt"]
    assert utils.find_all_files("foo/bar", ["*.txt"]) == []
    assert utils.find_all_files(".") == ["./foo/baz.txt", "./foo/bar/baz.txt"]
    assert utils.find_all_files(".", ["bar"]) == ["./foo/baz.txt"]
