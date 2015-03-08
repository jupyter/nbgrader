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

    # add the cell type
    m.update(str_to_bytes(cell.cell_type))

    # add whether it's a grade cell and/or solution cell
    m.update(str_to_bytes(str(is_grade(cell))))
    m.update(str_to_bytes(str(is_solution(cell))))

    # include the grade id and the number of points that the cell is worth
    if is_grade(cell):
        m.update(str_to_bytes(str(float(cell.metadata.nbgrader['points']))))
        m.update(str_to_bytes(cell.metadata.nbgrader['grade_id']))

    return m.hexdigest()
