from ...nbgraderformat.v1 import MetadataValidatorV1
from .. import (
    create_grade_cell,
    create_solution_cell)


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
