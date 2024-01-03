from nbformat import read as _read, reads as _reads
from nbformat import write as _write, writes as _writes
from nbformat.notebooknode import NotebookNode
import typing
from .v1 import MetadataValidatorV1
from .v2 import MetadataValidatorV2
from .common import BaseMetadataValidator, ValidationError
from nbformat.notebooknode import NotebookNode


class MetadataValidatorV3(BaseMetadataValidator):

    schema_version = 3

    def __init__(self) -> None:
        super().__init__()
        self.v1 = MetadataValidatorV1()
        self.v2 = MetadataValidatorV2()

    def _upgrade_v2_to_v3(self, cell: NotebookNode) -> NotebookNode:
        meta = cell.metadata['nbgrader']
        meta['schema_version'] = self.schema_version

        return cell

    def upgrade_cell_metadata(self, cell: NotebookNode) -> NotebookNode:
        if 'nbgrader' not in cell.metadata:
            return cell

        if 'schema_version' not in cell.metadata['nbgrader']:
            cell.metadata['nbgrader']['schema_version'] = 0

        if cell.metadata['nbgrader']['schema_version'] == 0:
            cell = self.v1._upgrade_v0_to_v1(cell)
            if 'nbgrader' not in cell.metadata:
                return cell

        if cell.metadata['nbgrader']['schema_version'] == 1:
            cell = self.v2._upgrade_v1_to_v2(cell)

        if cell.metadata['nbgrader']['schema_version'] == 2:
            cell = self._upgrade_v2_to_v3(cell)

        self._remove_extra_keys(cell)
        return cell

    def validate_cell(self, cell: NotebookNode) -> None:
        super(MetadataValidatorV3, self).validate_cell(cell)

        if 'nbgrader' not in cell.metadata:
            return

        meta = cell.metadata['nbgrader']
        grade = meta['grade']
        solution = meta['solution']
        locked = meta['locked']
        task = meta.get('task', False)

        # check if the cell type has changed
        if 'cell_type' in meta:
            if meta['cell_type'] != cell.cell_type:
                self.log.warning("Cell type has changed from {} to {}!".format(
                    meta['cell_type'], cell.cell_type), cell)

        # check for a valid grade id
        if grade or solution or locked:
            if 'grade_id' not in meta:
                raise ValidationError("nbgrader cell does not have a grade_id: {}".format(cell.source))
            if meta['grade_id'] == '':
                raise ValidationError("grade_id is empty")

        # check for valid points
        if grade:
            if 'points' not in meta:
                raise ValidationError("nbgrader cell '{}' does not have points".format(
                    meta['grade_id']))

        # check that markdown cells are grade AND solution (not either/or)
        if not task:
            if cell.cell_type == "markdown" and grade and not solution:
                raise ValidationError(
                    "Markdown grade cell '{}' is not marked as a solution cell".format(
                        meta['grade_id']))
            if cell.cell_type == "markdown" and not grade and solution:
                raise ValidationError(
                    "Markdown solution cell is not marked as a grade cell: {}".format(cell.source))
        else:
            if cell.cell_type != "markdown":
                raise ValidationError(
                    "Task cells have to be markdown: {}".format(cell.source))

    def validate_nb(self, nb: NotebookNode) -> None:
        super(MetadataValidatorV3, self).validate_nb(nb)

        ids = set([])
        for cell in nb.cells:

            if 'nbgrader' not in cell.metadata:
                continue

            grade = cell.metadata['nbgrader']['grade']
            solution = cell.metadata['nbgrader']['solution']
            locked = cell.metadata['nbgrader']['locked']

            if not grade and not solution and not locked:
                continue

            grade_id = cell.metadata['nbgrader']['grade_id']
            if grade_id in ids:
                raise ValidationError("Duplicate grade id: {}".format(grade_id))
            ids.add(grade_id)


def read_v3(source: typing.TextIO, as_version: int, **kwargs: typing.Any) -> NotebookNode:
    nb = _read(source, as_version, **kwargs)
    MetadataValidatorV3().validate_nb(nb)
    return nb


def write_v3(nb: NotebookNode, fp: typing.TextIO, **kwargs: typing.Any) -> None:
    MetadataValidatorV3().validate_nb(nb)
    _write(nb, fp, **kwargs)


def reads_v3(source: str, as_version: int, **kwargs: typing.Any) -> NotebookNode:
    nb = _reads(source, as_version, **kwargs)
    MetadataValidatorV3().validate_nb(nb)
    return nb


def writes_v3(nb: NotebookNode, **kwargs: typing.Any) -> None:
    MetadataValidatorV3().validate_nb(nb)
    _writes(nb, **kwargs)
