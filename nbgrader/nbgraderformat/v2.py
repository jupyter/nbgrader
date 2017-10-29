from nbformat import read as _read, reads as _reads
from nbformat import write as _write, writes as _writes
from .v1 import ValidatorV1
from .common import BaseValidator, ValidationError


class ValidatorV2(BaseValidator):

    schema = None

    def __init__(self):
        super(ValidatorV2, self).__init__(2)
        self.v1 = ValidatorV1()

    def _upgrade_v1_to_v2(self, cell):
        meta = cell.metadata['nbgrader']

        if 'cell_type' in meta:
            if not meta['cell_type']:
                del meta['cell_type']

        if 'checksum' in meta and 'cell_type' not in meta:
            self.log.warning("Cell has a checksum, but not a cell type! adding default cell type")
            meta['cell_type'] = cell.cell_type

        meta['schema_version'] = 2

        return cell

    def upgrade_cell_metadata(self, cell):
        if 'nbgrader' not in cell.metadata:
            return cell

        if 'schema_version' not in cell.metadata['nbgrader']:
            cell.metadata['nbgrader']['schema_version'] = 0

        if cell.metadata['nbgrader']['schema_version'] == 0:
            cell = self.v1._upgrade_v0_to_v1(cell)
            if 'nbgrader' not in cell.metadata:
                return cell

        if cell.metadata['nbgrader']['schema_version'] == 1:
            cell = self._upgrade_v1_to_v2(cell)

        return cell

    def validate_cell(self, cell):
        super(ValidatorV2, self).validate_cell(cell)

        if 'nbgrader' not in cell.metadata:
            return

        meta = cell.metadata['nbgrader']
        grade = meta['grade']
        solution = meta['solution']
        locked = meta['locked']

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
        if cell.cell_type == "markdown" and grade and not solution:
            raise ValidationError(
                "Markdown grade cell '{}' is not marked as a solution cell".format(
                    meta['grade_id']))
        if cell.cell_type == "markdown" and not grade and solution:
            raise ValidationError(
                "Markdown solution cell is not marked as a grade cell: {}".format(cell.source))

    def validate_nb(self, nb):
        super(ValidatorV2, self).validate_nb(nb)

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


def read_v2(source, as_version, **kwargs):
    nb = _read(source, as_version, **kwargs)
    ValidatorV2().validate_nb(nb)
    return nb


def write_v2(nb, fp, **kwargs):
    ValidatorV2().validate_nb(nb)
    return _write(nb, fp, **kwargs)


def reads_v2(source, as_version, **kwargs):
    nb = _reads(source, as_version, **kwargs)
    ValidatorV2().validate_nb(nb)
    return nb


def writes_v2(nb, **kwargs):
    ValidatorV2().validate_nb(nb)
    return _writes(nb, **kwargs)
