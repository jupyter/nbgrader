import hashlib
import autopep8

from IPython.utils.py3compat import str_to_bytes

def is_grade(cell):
    """Returns True if the cell is a grade cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('grade', False)


def is_solution(cell):
    """Returns True if the cell is a solution cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('solution', False)

def determine_grade(cell):
    if not is_grade(cell):
        raise ValueError("cell is not a grade cell")

    max_points = float(cell.metadata['nbgrader']['points'])
    if cell.cell_type == 'code':
        for output in cell.outputs:
            if output.output_type == 'error':
                return 0, max_points
        return max_points, max_points

    else:
        return None, max_points

def compute_checksum(cell):
    m = hashlib.md5()

    # fix minor whitespace issues that might have been added and then
    # add cell contents
    m.update(str_to_bytes(autopep8.fix_code(cell.source).rstrip()))

    # include number of points that the cell is worth
    if 'points' in cell.metadata.nbgrader:
        m.update(str_to_bytes(str(float(cell.metadata.nbgrader['points']))))

    # include the grade_id
    if 'grade_id' in cell.metadata.nbgrader:
        m.update(str_to_bytes(cell.metadata.nbgrader['grade_id']))

    return m.hexdigest()
