# coding: utf-8

import os
import pytest
import tempfile
import shutil
import zipfile

from nbformat.v4 import new_output
from os.path import join
from setuptools.archive_util import UnrecognizedFormat


from ... import utils
from .. import (
    create_code_cell,
    create_grade_cell, create_solution_cell,
    create_grade_and_solution_cell)

from .conftest import notwindows

@pytest.fixture
def temp_cwd(request):
    orig_dir = os.getcwd()
    path = tempfile.mkdtemp()
    os.chdir(path)

    def fin():
        os.chdir(orig_dir)
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

def test_get_partial_grade():
    # test single value in list
    test_data = { "data": { "text/plain": [ "0.6" ] } }
    assert utils.get_partial_grade(test_data,1.0) == 0.6

    # test single value not in list
    test_data = { "data": { "text/plain": "6.0" } }
    assert utils.get_partial_grade(test_data,10.0) == 6.0

    # test string in list, should assume partial credit not intended
    test_data = { "data": { "text/plain": [ "'this is a string'" ] } }
    assert utils.get_partial_grade(test_data,2.0) == 2.0

    # test returning too many points
    test_data = { "data": { "text/plain": [ "2.0" ] } }
    with pytest.raises(ValueError):
        utils.get_partial_grade(test_data, 1.0)

    test_data = { "fake_key": 4 }
    with pytest.raises(KeyError):
        utils.get_partial_grade(test_data, 2.0)

def test_determine_grade_code_partial_credit():
    # create grade cell with max_points == 5
    cell = create_grade_cell('test', "code", "foo", 5)
    test_data = {
        "text/plain": "3"
        }
    cell.outputs = [new_output(
        output_type="execute_result",
        execution_count=1,
        data=test_data)
        ]
    assert utils.determine_grade(cell) == (3,5)

    # should give error when partial_credit > max_grade
    cell.outputs = []
    test_data = {
        "text/plain": "5.5"
        }
    cell.outputs = [new_output(
        output_type="execute_result",
        execution_count=1,
        data=test_data)
        ]
    with pytest.raises(ValueError):
        utils.determine_grade(cell)

    cell.outputs = []
    test_data = {
        "text/plain": [ "0.5", "abc" ]
        }
    cell.outputs = [new_output(
        output_type="execute_result",
        execution_count=1,
        data=test_data)
        ]
    assert utils.determine_grade(cell) == (5,5)

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


def test_compute_checksum_utf8():
    utils.compute_checksum(create_solution_cell("\u03b8", "markdown", "foo"))
    utils.compute_checksum(create_solution_cell(u'$$\\int^\u221e_0 x^2dx$$', "markdown", "foo"))

def test_ignore_patterns(temp_cwd):
    dir = "foo"
    os.mkdir(dir)
    files = ["foo.txt", "long.txt", "truc.png"]
    for file in files:
        with open(join(dir, file), "w") as fh:
            fh.write("bar")
            if file == "long.txt":
                fh.write("x"*2000)
    os.mkdir(join(dir,"foo"))
    files.append("foo")
    assert utils.ignore_patterns(exclude=["foo*"])(dir, files) == ["foo.txt", "foo"]
    assert utils.ignore_patterns(include=["*.txt"])(dir, files) == ["truc.png"]
    assert utils.ignore_patterns(exclude=["foo.*"], include=["*.txt"])(dir, files) == ['foo.txt', 'truc.png']
    assert utils.ignore_patterns(max_file_size=2)(dir, files) == ["long.txt"]

def test_is_ignored(temp_cwd):
    os.mkdir("foo")
    with open(join("foo", "bar.txt"), "w") as fh:
        fh.write("bar")

    assert not utils.is_ignored("foo")
    assert utils.is_ignored(join("foo", "bar.txt"), ["*.txt"])
    assert utils.is_ignored(join("foo", "bar.txt"), ["bar.txt"])
    assert utils.is_ignored(join("foo", "bar.txt"), ["*"])
    assert not utils.is_ignored(join("foo", "bar.txt"), ["*.csv"])
    assert not utils.is_ignored(join("foo", "bar.txt"), ["foo"])
    assert not utils.is_ignored(join("foo", "bar.txt"), [join("foo", "*")])


def test_find_all_files(temp_cwd):
    os.makedirs(join("foo", "bar", "quux"))
    with open(join("foo", "baz.txt"), "w") as fh:
        fh.write("baz")
    with open(join("foo", "bar", "baz.txt"), "w") as fh:
        fh.write("baz")
    with open(join("foo", "bar", "quux", "baz.txt"), "w") as fh:
        fh.write("baz")

    assert utils.find_all_files("foo") == [
        join("foo", "baz.txt"),
        join("foo", "bar", "baz.txt"),
        join("foo", "bar", "quux", "baz.txt")]
    assert utils.find_all_files("foo", ["bar"]) == [join("foo", "baz.txt")]
    assert utils.find_all_files("foo", ["quux"]) == [
        join("foo", "baz.txt"),
        join("foo", "bar", "baz.txt")]
    assert utils.find_all_files(join("foo", "bar")) == [
        join("foo", "bar", "baz.txt"),
        join("foo", "bar", "quux", "baz.txt")]
    assert utils.find_all_files(join("foo", "bar"), ["*.txt"]) == []
    assert utils.find_all_files(".") == [
        join(".", "foo", "baz.txt"),
        join(".", "foo", "bar", "baz.txt"),
        join(".", "foo", "bar", "quux", "baz.txt")]
    assert utils.find_all_files(".", ["bar"]) == [join(".", "foo", "baz.txt")]
    assert utils.find_all_files(".", ["quux"]) == [
        join(".", "foo", "baz.txt"),
        join(".", "foo", "bar", "baz.txt")]


def test_unzip_invalid_ext(temp_cwd):
    with open(join("baz.txt"), "w") as fh:
        pass
    with pytest.raises(ValueError):
        utils.unzip("baz.txt", os.getcwd())


def test_unzip_bad_zip(temp_cwd):
    with open(join("baz.zip"), "wb") as fh:
        pass
    with pytest.raises(UnrecognizedFormat):
        utils.unzip("baz.zip", os.getcwd())


def test_unzip_no_output_path(temp_cwd):
    with open(join("baz.zip"), "wb") as fh:
        pass
    out = os.path.join(os.getcwd(), "blarg")
    with pytest.raises(OSError):
        utils.unzip("baz.zip", out)


def test_unzip_create_own_folder(temp_cwd):
    with open(join("foo.txt"), "w") as fh:
        fh.write("foo")
    with zipfile.ZipFile("baz.zip", "w") as fh:
        fh.write("foo.txt")

    utils.unzip("baz.zip", os.getcwd())
    assert not os.path.isdir("baz")

    utils.unzip("baz.zip", os.getcwd(), create_own_folder=True)
    assert os.path.isdir("baz")
    assert os.path.isfile(os.path.join("baz", "foo.txt"))


def test_unzip_tree(temp_cwd):
    with open(join("foo.txt"), "w") as fh:
        fh.write("foo")

    with zipfile.ZipFile("baz.zip", "w") as fh:
        fh.write("foo.txt", os.path.join("bar", "foo.txt"))
        fh.write("foo.txt")

    with zipfile.ZipFile("data.zip", "w") as fh:
        fh.write("foo.txt", os.path.join("bar", "foo.txt"))
        fh.write("foo.txt")
        fh.write("baz.zip")  # must also get unzipped

    utils.unzip("data.zip", os.getcwd(), create_own_folder=True, tree=True)
    assert os.path.isdir("data")
    assert os.path.isdir(os.path.join("data", "baz"))
    assert os.path.isdir(os.path.join("data", "bar"))
    assert os.path.isdir(os.path.join("data", "baz", "bar"))
    assert os.path.isfile(os.path.join("data", "baz", "bar", "foo.txt"))

@notwindows
def test_get_username():
    assert utils.get_username() == os.environ["USER"]
    # Can't test get_username's support for JUPYTERHUB_USER, as
    # this would require actually running the tests as 'jovyan'.
