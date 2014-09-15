from jinja2 import Environment


def get_assignment_cell_type(cell):
    """Get the assignment cell type from the assignment metadata."""
    if 'nbgrader' not in cell.metadata:
        return ''
    if 'cell_type' not in cell.metadata['nbgrader']:
        return ''
    return cell.metadata['nbgrader']['cell_type']


def is_gradeable(cell):
    """Returns True if the cell is a gradeable cell."""
    return get_assignment_cell_type(cell) == 'grade'


def is_solution(cell):
    """Returns True if the cell is a solution-only cell."""
    return get_assignment_cell_type(cell) == 'solution'


def is_release(cell):
    """Returns True if the cell is a release-only cell."""
    return get_assignment_cell_type(cell) == 'release'


def is_skip(cell):
    """Returns True if the cell should be skipped."""
    return get_assignment_cell_type(cell) == 'skip'


def is_test(cell):
    """Returns True if the cell is a test cell."""
    return get_assignment_cell_type(cell) == 'test'


def make_jinja_environment():
    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=False)
    return env
