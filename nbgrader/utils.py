def get_assignment_cell_type(cell):
    """Get the assignment cell type from the assignment metadata."""
    if 'nbgrader' not in cell.metadata:
        return ''
    if 'cell_type' not in cell.metadata['nbgrader']:
        return ''
    return cell.metadata['nbgrader']['cell_type']


def is_grade(cell):
    """Returns True if the cell is a grade cell."""
    return get_assignment_cell_type(cell) == 'grade'


def is_solution(cell):
    """Returns True if the cell is a solution-only cell."""
    return get_assignment_cell_type(cell) == 'solution'
