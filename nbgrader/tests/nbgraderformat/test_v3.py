import json
import os
import pytest
import tempfile
from nbformat import current_nbformat, read
from nbformat.v4 import new_notebook
from ...nbgraderformat.common import SchemaMismatchError, ValidationError
from ...nbgraderformat.v3 import (
    MetadataValidatorV3, read_v3, reads_v3, write_v3, writes_v3)
from .. import (
    create_code_cell,
    create_grade_cell,
    create_solution_cell,
    create_task_cell,
    create_regular_cell)


def test_set_false():
    cell = create_grade_cell("", "code", "foo", 2, 0)
    del cell.metadata.nbgrader["solution"]
    del cell.metadata.nbgrader["locked"]

    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert not cell.metadata.nbgrader["solution"]
    assert not cell.metadata.nbgrader["locked"]

    cell = create_solution_cell("", "code", "foo", 0)
    del cell.metadata.nbgrader["grade"]
    del cell.metadata.nbgrader["locked"]

    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert not cell.metadata.nbgrader["grade"]
    assert not cell.metadata.nbgrader["locked"]


def test_remove_metadata():
    cell = create_solution_cell("", "code", "foo", 0)
    cell.metadata.nbgrader["solution"] = False

    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "nbgrader" not in cell.metadata


def test_remove_points():
    cell = create_solution_cell("", "code", "foo", 0)
    cell.metadata.nbgrader["points"] = 2

    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "points" not in cell.metadata.nbgrader


def test_set_points():
    cell = create_grade_cell("", "code", "foo", "", 0)
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0

    cell = create_grade_cell("", "code", "foo", "1.5", 0)
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 1.5

    cell = create_grade_cell("", "code", "foo", 1, 0)
    del cell.metadata.nbgrader["points"]
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0

    cell = create_grade_cell("", "code", "foo", -1, 0)
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["points"] == 0.0


def test_extra_keys():
    cell = create_grade_cell("", "code", "foo", "", 0)
    cell.metadata.nbgrader["foo"] = "bar"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "foo" not in cell.metadata.nbgrader

    cell = create_grade_cell("", "code", "foo", "", 1)
    cell.metadata.nbgrader["foo"] = "bar"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "foo" not in cell.metadata.nbgrader

    cell = create_grade_cell("", "code", "foo", "", 2)
    cell.metadata.nbgrader["foo"] = "bar"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "foo" not in cell.metadata.nbgrader


def test_schema_version():
    cell = create_grade_cell("", "code", "foo", "", 0)
    del cell.metadata.nbgrader["schema_version"]
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader["schema_version"] == 3


def test_cell_type():
    cell = create_grade_cell("", "code", "foo", "", 0)
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert "cell_type" not in cell.metadata.nbgrader

    cell = create_grade_cell("", "code", "foo", "", 0)
    cell.metadata.nbgrader["checksum"] = "abcd"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader['cell_type'] == "code"

    cell = create_grade_cell("", "code", "foo", "", 0)
    cell.metadata.nbgrader["checksum"] = "abcd"
    cell.metadata.nbgrader["cell_type"] = "markdown"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader['cell_type'] == "markdown"

    cell = create_grade_cell("", "code", "foo", "", 0)
    cell.metadata.nbgrader["checksum"] = "abcd"
    cell.metadata.nbgrader["cell_type"] = "code"
    MetadataValidatorV3().upgrade_cell_metadata(cell)
    assert cell.metadata.nbgrader['cell_type'] == "code"


def test_task_value():
    cell = create_task_cell("this is a task cell", "markdown", "foo", 0)
    assert cell.metadata.nbgrader['task']

    cell = create_grade_cell("", "code", "foo", "")
    assert not cell.metadata.nbgrader['task']

    cell = create_grade_cell("", "code", "foo", "")
    assert not cell.metadata.nbgrader['task']

    cell = create_solution_cell("", "code", "foo")
    assert not cell.metadata.nbgrader['task']


def test_read():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    read_v3(path, current_nbformat)


def test_reads():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    contents = open(path, "r").read()
    reads_v3(contents, current_nbformat)


def test_write():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    nb = read_v3(path, current_nbformat)
    with tempfile.TemporaryFile(mode="w") as fh:
        write_v3(nb, fh)


def test_writes():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    nb = read_v3(path, current_nbformat)
    writes_v3(nb)


def test_too_old():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v0.ipynb")
    with pytest.raises(SchemaMismatchError):
        read_v3(path, current_nbformat)


def test_too_new():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test.ipynb")
    nb = read_v3(path, current_nbformat)
    for cell in nb.cells:
        if hasattr(cell.metadata, "nbgrader"):
            cell.metadata.nbgrader.schema_version += 1
    nb = json.dumps(nb)
    with pytest.raises(SchemaMismatchError):
        reads_v3(nb, current_nbformat)


def test_upgrade_notebook_metadata():
    currdir = os.path.split(__file__)[0]
    path = os.path.join(currdir, "..", "apps", "files", "test-v0.ipynb")
    with open(path, "r") as fh:
        nb = read(fh, current_nbformat)
    nb = MetadataValidatorV3().upgrade_notebook_metadata(nb)


def test_upgrade_cell_metadata():
    cell = create_grade_cell("", "code", "foo", 5, 0)
    MetadataValidatorV3().upgrade_cell_metadata(cell)

    cell = create_grade_cell("", "code", "foo", 5, 3)
    MetadataValidatorV3().upgrade_cell_metadata(cell)

    cell = create_grade_cell("", "code", "foo", 5, 4)
    MetadataValidatorV3().upgrade_cell_metadata(cell)


def test_regular_cells():
    validator = MetadataValidatorV3()

    # code cell without nbgrader metadata
    cell = create_code_cell()
    validator.validate_cell(cell)
    validator.upgrade_cell_metadata(cell)

    # code cell with metadata, but not an nbgrader cell
    cell = create_regular_cell("", "code", schema_version=3)
    validator.validate_cell(cell)

    nb = new_notebook()
    cell1 = create_code_cell()
    cell2 = create_regular_cell("", "code", schema_version=3)
    nb.cells = [cell1, cell2]
    validator.validate_nb(nb)


def test_invalid_metadata():
    validator = MetadataValidatorV3()

    # make sure the default cell works ok
    cell = create_grade_cell("", "code", "foo", 5, 3)
    validator.validate_cell(cell)

    # missing grade_id
    cell = create_grade_cell("", "code", "foo", 5, 3)
    del cell.metadata.nbgrader["grade_id"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # grade_id is empty
    cell = create_grade_cell("", "code", "", 5, 3)
    del cell.metadata.nbgrader["task"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # missing points
    cell = create_grade_cell("", "code", "foo", 5, 3)
    del cell.metadata.nbgrader["points"]
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # markdown grade cell not marked as a solution cell
    cell = create_grade_cell("", "markdown", "foo", 5, 3)
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # markdown solution cell not marked as a grade cell
    cell = create_solution_cell("", "markdown", "foo", 3)
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)

    # task cell shouldn't be a code cell
    cell = create_task_cell("", "markdown", "foo", 5, 3)
    validator.validate_cell(cell)

    # task cell shouldn't be able to be a code cell
    cell = create_task_cell("", "code", "foo", 5, 3)
    with pytest.raises(ValidationError):
        validator.validate_cell(cell)


def test_duplicate_cells():
    validator = MetadataValidatorV3()
    nb = new_notebook()
    cell1 = create_grade_cell("", "code", "foo", 5, 3)
    cell2 = create_grade_cell("", "code", "foo", 5, 3)
    nb.cells = [cell1, cell2]
    with pytest.raises(ValidationError):
        validator.validate_nb(nb)


def test_celltype_changed(caplog):
    cell = create_solution_cell("", "code", "foo", 3)
    cell.metadata.nbgrader["cell_type"] = "code"
    MetadataValidatorV3().validate_cell(cell)
    assert "Cell type has changed from markdown to code!" not in caplog.text

    cell = create_solution_cell("", "code", "foo", 3)
    cell.metadata.nbgrader["cell_type"] = "markdown"
    MetadataValidatorV3().validate_cell(cell)
    assert "Cell type has changed from markdown to code!" in caplog.text
