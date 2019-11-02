import os
import pytest
import tempfile
from nbformat import current_nbformat, read
from nbformat.v4 import new_notebook
from ...nbgraderformat.common import SchemaMismatchError, ValidationError
from ...nbgraderformat.v1 import (
    MetadataValidatorV1, read_v1, reads_v1, write_v1, writes_v1)
from .. import (
    create_code_cell,
    create_grade_cell,
    create_solution_cell,
    create_regular_cell)


def test_set_false():
    cell = create_grade_cell("", "code", "foo", 2, 0)
    del cell.metadata.nbgrader["solution"]
    del cell.metadata.nbgrader["locked"]

    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert not cell.metadata.nbgrader["solution"]
    assert not cell.metadata.nbgrader["locked"]

    cell = create_solution_cell("", "code", "foo", 0)
    del cell.metadata.nbgrader["grade"]
    del cell.metadata.nbgrader["locked"]

    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert not cell.metadata.nbgrader["grade"]
    assert not cell.metadata.nbgrader["locked"]


def test_remove_metadata():
    cell = create_solution_cell("", "code", "foo", 0)
    cell.metadata.nbgrader["solution"] = False

    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert "nbgrader" not in cell.metadata


def test_remove_points():
    cell = create_solution_cell("", "code", "foo", 0)
    cell.metadata.nbgrader["points"] = 2

    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert "points" not in cell.metadata.nbgrader


def test_set_points():
    cell = create_grade_cell("", "code", "foo", "", 0)
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0

    cell = create_grade_cell("", "code", "foo", "1.5", 0)
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 1.5

    cell = create_grade_cell("", "code", "foo", 1, 0)
    del cell.metadata.nbgrader["points"]
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0

    cell = create_grade_cell("", "code", "foo", -1, 0)
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0


def test_extra_keys():
    cell = create_grade_cell("", "code", "foo", "", 0)
    cell.metadata.nbgrader["foo"] = "bar"
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert "foo" not in cell.metadata.nbgrader


def test_schema_version():
    cell = create_grade_cell("", "code", "foo", "", 0)
    del cell.metadata.nbgrader["schema_version"]
    MetadataValidatorV1().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["schema_version"] == 1


def test_read():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v1.ipynb")
    read_v1(path, current_nbformat)


def test_reads():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v1.ipynb")
    contents = open(path, "r").read()
    reads_v1(contents, current_nbformat)


def test_write():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v1.ipynb")
    nb = read_v1(path, current_nbformat)
    with tempfile.TemporaryFile(mode="w") as fh:
        write_v1(nb, fh)


def test_writes():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v1.ipynb")
    nb = read_v1(path, current_nbformat)
    writes_v1(nb)


def test_too_old():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v0.ipynb")
    with pytest.raises(SchemaMismatchError):
        read_v1(path, current_nbformat)


def test_too_new():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    with pytest.raises(SchemaMismatchError):
        read_v1(path, current_nbformat)


def test_upgrade_notebook_metadata():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v0.ipynb")
    with open(path, "r") as fh:
        nb = read(fh, current_nbformat)
    nb = MetadataValidatorV1().upgrade_notebook_metadata(nb)


def test_upgrade_cell_metadata():
    cell = create_grade_cell("", "code", "foo", 5, 0)
    MetadataValidatorV1().upgrade_cell_metadata(cell)

    cell = create_grade_cell("", "code", "foo", 5, 1)
    MetadataValidatorV1().upgrade_cell_metadata(cell)

    cell = create_grade_cell("", "code", "foo", 5, 2)
    MetadataValidatorV1().upgrade_cell_metadata(cell)


def test_regular_cells():
    validator = MetadataValidatorV1()

    # code cell without nbgrader metadata
    cell = create_code_cell()
    validator.validate_cell(cell)
    validator.upgrade_cell_metadata(cell)

    # code cell with metadata, but not an nbgrader cell
    cell = create_regular_cell("", "code", schema_version=1)
    del cell.metadata.nbgrader["task"]
    validator.validate_cell(cell)

    nb = new_notebook()
    cell1 = create_code_cell()
    cell2 = create_regular_cell("", "code", schema_version=1)
    del cell2.metadata.nbgrader["task"]
    nb.cells = [cell1, cell2]
    validator.validate_nb(nb)


def test_invalid_metadata():
    validator = MetadataValidatorV1()

    # make sure the default cell works ok
    cell = create_grade_cell("", "code", "foo", 5, 1)
    del cell.metadata.nbgrader["task"]
    validator.validate_cell(cell)

    # missing grade_id
    cell = create_grade_cell("", "code", "foo", 5, 1)
    del cell.metadata.nbgrader["task"]
    del cell.metadata.nbgrader["grade_id"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # grade_id is empty
    cell = create_grade_cell("", "code", "", 5, 1)
    del cell.metadata.nbgrader["task"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # missing points
    cell = create_grade_cell("", "code", "foo", 5, 1)
    del cell.metadata.nbgrader["task"]
    del cell.metadata.nbgrader["points"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # markdown grade cell not marked as a solution cell
    cell = create_grade_cell("", "markdown", "foo", 5, 1)
    del cell.metadata.nbgrader["task"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # markdown solution cell not marked as a grade cell
    cell = create_solution_cell("", "markdown", "foo", 1)
    del cell.metadata.nbgrader["task"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)


def test_duplicate_cells():
    validator = MetadataValidatorV1()
    nb = new_notebook()
    cell1 = create_grade_cell("", "code", "foo", 5, 1)
    del cell1.metadata.nbgrader["task"]
    cell2 = create_grade_cell("", "code", "foo", 5, 1)
    del cell2.metadata.nbgrader["task"]
    nb.cells = [cell1, cell2]
    with pytest.raises(ValidationError):
        validator.validate_nb(nb)
