import pytest

from datetime import datetime, timedelta
from ... import api
from ... import utils
from ...api import InvalidEntry, MissingEntry
from sqlalchemy import select, func, exists, case, literal_column


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


#### Test task cells

def test_add_task_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_task_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
    assert gc.name == 'test1'
    assert gc.max_score == 2
    assert gc.cell_type == 'markdown'
    assert n.task_cells == [gc]
    assert gc.notebook == n



def test_add_task_cell_with_args(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_task_cell(
        'test1', 'p1', 'foo',
        max_score=3, cell_type="code")
    assert gc.name == 'test1'
    assert gc.max_score == 3
    assert gc.cell_type == "code"


def test_create_invalid_task_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_task_cell(
            'test1', 'p1', 'foo',
            max_score=3, cell_type="something")


def test_add_duplicate_task_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_task_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    with pytest.raises(InvalidEntry):
        gradebook.add_task_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')


def test_find_task_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.add_task_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    assert gradebook.find_task_cell('test1', 'p1', 'foo') == gc1

    gc2 = gradebook.add_task_cell('test2', 'p1', 'foo', max_score=2, cell_type='code')
    assert gradebook.find_task_cell('test1', 'p1', 'foo') == gc1
    assert gradebook.find_task_cell('test2', 'p1', 'foo') == gc2


def test_find_nonexistant_task_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_task_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_task_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_task_cell('test1', 'p1', 'foo')


def test_update_or_create_task_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.update_or_create_task_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
    assert gc1.max_score == 2
    assert gc1.cell_type == 'markdown'
    assert gradebook.find_task_cell('test1', 'p1', 'foo') == gc1

    # now test finding/updating it
    gc2 = gradebook.update_or_create_task_cell('test1', 'p1', 'foo', max_score=3)
    assert gc1 == gc2
    assert gc1.max_score == 3
    assert gc1.cell_type == 'markdown'

def test_find_graded_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_assignment('foo2')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_notebook('p2', 'foo2')
    gc1 = gradebook.update_or_create_task_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
    assert gc1.max_score == 2
    assert gc1.cell_type == 'markdown'
    assert gradebook.find_graded_cell('test1', 'p1', 'foo') == gc1
    print (gc1)
    gc2 = gradebook.update_or_create_grade_cell('test2', 'p2', 'foo2', max_score=2, cell_type='code')
    print (type(gc2))
    assert gc2.max_score == 2
    assert gc2.cell_type == 'code'
    assert gradebook.find_grade_cell('test2', 'p2', 'foo2') == gc2
    assert gradebook.find_graded_cell('test2', 'p2', 'foo2') == gc2


def test_grade_cell_maxscore(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.update_or_create_task_cell('test1', 'p1', 'foo', max_score=1000, cell_type='markdown')
    gc1a = gradebook.update_or_create_task_cell('test1a', 'p1', 'foo', max_score=3000, cell_type='markdown')
    gc2 = gradebook.update_or_create_grade_cell('test2', 'p1', 'foo', max_score=5, cell_type='code')
    gc3 = gradebook.update_or_create_grade_cell('test3', 'p1', 'foo', max_score=7, cell_type='code')
    gc4 = gradebook.update_or_create_grade_cell('test4', 'p1', 'foo', max_score=13, cell_type='code')
    gc5 = gradebook.update_or_create_grade_cell('test5', 'p1', 'foo', max_score=10, cell_type='code')
    print (gradebook.db.query(api.GradeCell.notebook_id)\
        #.filter(api.GradeCell.notebook_id == api.Notebook.id)
        .all()
    )
    #assert gc2.max_score == 5
    n1=gradebook.find_notebook('p1','foo')
    assert n1.max_score_gradecell == 35
    assert n1.max_score_taskcell == 4000
    assert n1.max_score == 4035
