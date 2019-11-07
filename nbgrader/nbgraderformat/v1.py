from nbformat import read as _read, reads as _reads
from nbformat import write as _write, writes as _writes
from nbformat.notebooknode import NotebookNode
from .common import BaseMetadataValidator, ValidationError
import typing


class MetadataValidatorV1(BaseMetadataValidator):

    schema_version = 1

    def __init__(self) -> None:
        super().__init__()

    def _upgrade_v0_to_v1(self, cell: NotebookNode) -> NotebookNode:
        meta = cell.metadata['nbgrader']

        if 'grade' not in meta:
            meta['grade'] = False
        if 'solution' not in meta:
            meta['solution'] = False
        if 'locked' not in meta:
            meta['locked'] = False

        if not meta['grade'] and not meta['solution'] and not meta['locked']:
            del cell.metadata['nbgrader']
            return cell

        if not meta['grade']:
            if 'points' in meta:
                del meta['points']
        elif 'points' in meta:
            if meta['points'] == '':
                meta['points'] = 0.0
            else:
                points = float(meta['points'])
                if points < 0:
                    meta['points'] = 0.0
                else:
                    meta['points'] = float(meta['points'])
        else:
            meta['points'] = 0.0

        meta['schema_version'] = self.schema_version

        return cell

    def upgrade_cell_metadata(self, cell: NotebookNode) -> NotebookNode:
        if 'nbgrader' not in cell.metadata:
            return cell

        if 'schema_version' not in cell.metadata['nbgrader']:
            cell.metadata['nbgrader']['schema_version'] = 0

        if cell.metadata['nbgrader']['schema_version'] == 0:
            cell = self._upgrade_v0_to_v1(cell)

        if 'nbgrader' not in cell.metadata:
            return cell

        self._remove_extra_keys(cell)
        return cell

    def validate_cell(self, cell: NotebookNode) -> None:
        super(MetadataValidatorV1, self).validate_cell(cell)

        if 'nbgrader' not in cell.metadata:
            return

        meta = cell.metadata['nbgrader']
        grade = meta['grade']
        solution = meta['solution']
        locked = meta['locked']

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
        if cell.cell_type == "markdown" and grade and not solution:
            raise ValidationError(
                "Markdown grade cell '{}' is not marked as a solution cell".format(
                    meta['grade_id']))
        if cell.cell_type == "markdown" and not grade and solution:
            raise ValidationError(
                "Markdown solution cell is not marked as a grade cell: {}".format(cell.source))

    def validate_nb(self, nb: NotebookNode) -> None:
        super(MetadataValidatorV1, self).validate_nb(nb)

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


def read_v1(source: typing.io.TextIO, as_version: int, **kwargs: typing.Any) -> NotebookNode:
    nb = _read(source, as_version, **kwargs)
    MetadataValidatorV1().validate_nb(nb)
    return nb


def write_v1(nb: NotebookNode, fp: typing.io.TextIO, **kwargs: typing.Any) -> None:
    MetadataValidatorV1().validate_nb(nb)
    _write(nb, fp, **kwargs)


def reads_v1(source: str, as_version: int, **kwargs: typing.Any) -> NotebookNode:
    nb = _reads(source, as_version, **kwargs)
    MetadataValidatorV1().validate_nb(nb)
    return nb


def writes_v1(nb: NotebookNode, **kwargs: typing.Any) -> None:
    MetadataValidatorV1().validate_nb(nb)
    _writes(nb, **kwargs)
