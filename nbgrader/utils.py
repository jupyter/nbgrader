import hashlib
import autopep8
import dateutil.parser

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

    elif is_solution(cell):
        # if it's a solution cell and the checksum hasn't changed, that means
        # they didn't provide a response, so we can automatically give this a
        # zero grade
        if "checksum" in cell.metadata.nbgrader and cell.metadata.nbgrader["checksum"] == compute_checksum(cell):
            return 0, max_points
        else:
            return None, max_points

    else:
        return None, max_points

def compute_checksum(cell):
    m = hashlib.md5()

    # if it's a code cell, then fix minor whitespace issues that might have been 
    # added and then add cell contents; otherwise just add cell contents
    if cell.cell_type == "code":
        m.update(str_to_bytes(autopep8.fix_code(cell.source).rstrip()))
    else:
        m.update(str_to_bytes(cell.source.strip()))

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

def parse_utc(ts):
    """Parses a timestamp into datetime format, converting it to UTC if necessary."""
    if isinstance(ts, str):
        ts = dateutil.parser.parse(ts)
    if ts.tzinfo is not None:
        ts = (ts - ts.utcoffset()).replace(tzinfo=None)
    return ts
