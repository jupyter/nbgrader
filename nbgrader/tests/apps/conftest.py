import os
import tempfile
import shutil
import pytest

from nbgrader.api import Gradebook


@pytest.fixture
def db(request):
    path = tempfile.mkdtemp()
    dbpath = os.path.join(path, "nbgrader_test.db")

    def fin():
        shutil.rmtree(path)
    request.addfinalizer(fin)

    return "sqlite:///" + dbpath


@pytest.fixture
def gradebook(db):
    gb = Gradebook(db)
    gb.add_assignment("ps1", duedate="2015-02-02 14:58:23.948203 PST")
    gb.add_student("foo")
    gb.add_student("bar")
    return db


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


@pytest.fixture
def temp_dir(request):
    path = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(path)
    request.addfinalizer(fin)

    return path


@pytest.fixture
def exchange(request):
    path = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(path)
    request.addfinalizer(fin)

    return path
