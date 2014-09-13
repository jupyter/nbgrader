def get_assignment_cell_type(cell):
    """Get the assignment cell type from the assignment metadata."""
    if 'nbgrader' not in cell.metadata:
        return ''
    if 'cell_type' not in cell.metadata['nbgrader']:
        return ''
    return cell.metadata['nbgrader']['cell_type']

def is_solution(cell):
    return get_assignment_cell_type(cell) == 'solution'

def is_test(cell):
    return get_assignment_cell_type(cell) == 'test'
