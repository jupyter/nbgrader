import pytest

from datetime import datetime, timedelta
from ... import api
from ... import utils
from ...api import InvalidEntry, MissingEntry

@pytest.fixture
def gradebook(request):
    gb = api.Gradebook("sqlite:///:memory:")
    def fin():
        gb.close()
    request.addfinalizer(fin)
    return gb


@pytest.fixture
def assignment(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_task_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    gradebook.add_task_cell('test2', 'p1', 'foo', max_score=2, cell_type='markdown')
    gradebook.add_solution_cell('solution1', 'p1', 'foo')
    gradebook.add_solution_cell('test2', 'p1', 'foo')
    gradebook.add_source_cell('test1', 'p1', 'foo', cell_type='code')
    gradebook.add_source_cell('test2', 'p1', 'foo', cell_type='markdown')
    gradebook.add_source_cell('solution1', 'p1', 'foo', cell_type='code')
    return gradebook


def test_find_taskgrade(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    taskgrades = n1.taskgrades

    for g1 in taskgrades:
        g2 = assignment.find_taskgrade(g1.name, 'p1', 'foo', 'hacker123')
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_taskgrade('asdf', 'p1', 'foo', 'hacker123')


def test_find_taskgrade_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    taskgrades = n1.taskgrades

    for g1 in taskgrades:
        g2 = assignment.find_taskgrade_by_id(g1.id)
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_taskgrade_by_id('12345')


def test_find_taskcomment(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    taskcomments = n1.taskcomments

    for c1 in taskcomments:
        c2 = assignment.find_taskcomment(c1.name, 'p1', 'foo', 'hacker123')
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_taskcomment('asdf', 'p1', 'foo', 'hacker123')


def test_find_taskcomment_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    taskcomments = n1.taskcomments

    for c1 in taskcomments:
        c2 = assignment.find_taskcomment_by_id(c1.id)
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_taskcomment_by_id('12345')


