import pytest

from datetime import datetime, timedelta
from ... import api
from ... import utils
from ...api import InvalidEntry, MissingEntry
from _pytest.fixtures import SubRequest
from nbgrader.api import Gradebook


@pytest.fixture
def gradebook(request: SubRequest) -> Gradebook:
    gb = api.Gradebook("sqlite:///:memory:")

    def fin() -> None:
        gb.close()
    request.addfinalizer(fin)
    return gb


@pytest.fixture
def assignment(gradebook: Gradebook) -> Gradebook:
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    gradebook.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='markdown')
    gradebook.add_solution_cell('solution1', 'p1', 'foo')
    gradebook.add_solution_cell('test2', 'p1', 'foo')
    gradebook.add_source_cell('test1', 'p1', 'foo', cell_type='code')
    gradebook.add_source_cell('test2', 'p1', 'foo', cell_type='markdown')
    gradebook.add_source_cell('solution1', 'p1', 'foo', cell_type='code')
    return gradebook


def makeAssignments(gb, na, nn, ns, grades=[1, 2, 10, 20, 100, 200]):
    for si in range(ns):
        sname = "s{0}".format(si + 1)
        gb.add_student(sname)
    for ia in range(na):
        aname = 'a{0}'.format(ia + 1)
        a = gb.add_assignment(aname)
        for ni in range(nn):
            nname = 'n{0}'.format(ni + 1)
            n = gb.add_notebook(nname, aname)
            gb.add_solution_cell('solution1', nname, aname)
            gb.add_solution_cell('solution2', nname, aname)
            gb.add_source_cell('source1', nname, aname, cell_type='code')
            gb.add_source_cell('source2', nname, aname, cell_type='markdown')
            gb.add_source_cell('solution1', nname, aname, cell_type='code')
            gb.add_grade_cell('grade_code1', nname, aname, cell_type='code', max_score=2)
            gb.add_grade_cell('grade_code2', nname, aname, cell_type='code', max_score=3)
            gb.add_grade_cell('grade_written1', nname, aname, cell_type='markdown', max_score=20)
            gb.add_grade_cell('grade_written2', nname, aname, cell_type='markdown', max_score=30)
            gb.add_task_cell('task1', nname, aname, cell_type='markdown', max_score=200)
            gb.add_task_cell('task2', nname, aname, cell_type='markdown', max_score=300)
        for si in range(ns):
            sname = "s{0}".format(si + 1)
            sub = gb.add_submission(aname, sname)
            sub.flagged = False
            for ni in range(nn):
                nname = 'n{0}'.format(ni + 1)
                g1 = gb.find_grade("grade_code1", nname, aname, sname)
                g2 = gb.find_grade("grade_code2", nname, aname, sname)
                g3 = gb.find_grade("grade_written1", nname, aname, sname)
                g4 = gb.find_grade("grade_written2", nname, aname, sname)
                g5 = gb.find_grade("task1", nname, aname, sname)
                g6 = gb.find_grade("task2", nname, aname, sname)

                (g1.manual_score, g2.manual_score, g3.manual_score, g4.manual_score,
                 g5.manual_score, g6.manual_score) = grades
            gb.db.commit()

    return gb


@pytest.fixture
def FiveStudents(gradebook):
    return makeAssignments(gradebook, 1, 1, 5)


@pytest.fixture
def FiveNotebooks(gradebook):
    return makeAssignments(gradebook, 1, 5, 1)


@pytest.fixture
def FiveAssignments(gradebook):
    return makeAssignments(gradebook, 5, 1, 1)


@pytest.fixture
def assignmentWithTask(gradebook: Gradebook) -> Gradebook:
    for f in ['foo', 'foo2']:
        gradebook.add_assignment(f)
        for n in ['p1', 'p2']:
            gradebook.add_notebook(n, f)
            gradebook.add_solution_cell('solution1', n, f)
            gradebook.add_solution_cell('test2', n, f)
            gradebook.add_source_cell('test1', n, f, cell_type='code')
            gradebook.add_source_cell('test2', n, f, cell_type='markdown')
            gradebook.add_source_cell('solution1', n, f, cell_type='code')
            gradebook.add_grade_cell('grade_code1', n, f, cell_type='code', max_score=1)
            gradebook.add_grade_cell('grade_code2', n, f, cell_type='code', max_score=10)
            gradebook.add_grade_cell('grade_written1', n, f, cell_type='markdown', max_score=1)
            gradebook.add_grade_cell('grade_written2', n, f, cell_type='markdown', max_score=10)
            gradebook.add_task_cell('task1', n, f, cell_type='markdown', max_score=2)
            gradebook.add_task_cell('task2', n, f, cell_type='markdown', max_score=20)

    return gradebook


@pytest.fixture
def assignmentWithSubmissionNoMarks(assignmentWithTask: Gradebook) -> Gradebook:
    assignmentWithTask.add_student('hacker123')
    assignmentWithTask.add_student('bitdiddle')
    assignmentWithTask.add_student('louisreasoner')
    s1 = assignmentWithTask.add_submission('foo', 'hacker123')
    s2 = assignmentWithTask.add_submission('foo', 'bitdiddle')
    s1.flagged = True
    s2.flagged = False
    assignmentWithTask.db.commit()
    return assignmentWithTask

possiblegrades = [
    [0.5, 2, 3, 5, 1, 7, 2, 1],
    [0.1, 4, 0.25, 1, 7, 0.0, 1, 1],
    [0] * 8,
    [2] * 8,
    [0.25] * 8,
]


@pytest.fixture(params=possiblegrades)
def assignmentWithSubmissionWithMarks(assignmentWithSubmissionNoMarks: Gradebook, request: SubRequest) -> Gradebook:
    a = assignmentWithSubmissionNoMarks
    g1 = a.find_grade("grade_code1", "p1", "foo", "bitdiddle")
    g2 = a.find_grade("grade_code2", "p1", "foo", "bitdiddle")

    g3 = a.find_grade("grade_written1", "p1", "foo", "hacker123")
    g4 = a.find_grade("grade_written2", "p1", "foo", "hacker123")

    g5 = a.find_grade("task1", "p1", "foo", "bitdiddle")
    g6 = a.find_grade("task2", "p1", "foo", "bitdiddle")
    g7 = a.find_grade("task1", "p1", "foo", "hacker123")
    g8 = a.find_grade("task2", "p1", "foo", "hacker123")

    (g1.manual_score, g2.manual_score, g3.manual_score, g4.manual_score, g5.manual_score,
     g6.manual_score, g7.manual_score, g8.manual_score) = request.param
    a.db.commit()
    a.usedgrades = request.param
    a.usedgrades_code = request.param[:2]
    a.usedgrades_written = request.param[2:4]
    a.usedgrades_task = request.param[4:]

    return a


@pytest.fixture
def assignmentManyStudents(assignmentWithTask, request):
    a = assignmentWithTask
    for s in range(50):
        sname = 's{0}'.format(s)
        a.add_student(sname)
        sub = a.add_submission('foo', sname)
        g1 = a.find_grade("grade_code1", "p1", "foo", sname)
        g2 = a.find_grade("grade_written1", "p1", "foo", sname)
        g3 = a.find_grade("task1", "p1", "foo", sname)
        g4 = a.find_grade("task2", "p1", "foo", sname)

        (
            g1.manual_score,
            g2.manual_score,
            g3.manual_score,
            g4.manual_score) = (1, 2, 3, 4)
    a.db.commit()

    return a


@pytest.fixture
def assignmentTwoStudents(assignmentWithTask, request):
    a = assignmentWithTask
    for s in range(50):
        sname = 's{0}'.format(s)
        a.add_student(sname)
        sub = a.add_submission('foo', sname)
        g1 = a.find_grade("grade_code1", "p1", "foo", sname)
        g2 = a.find_grade("grade_written1", "p1", "foo", sname)
        g3 = a.find_grade("task1", "p1", "foo", sname)
        g4 = a.find_grade("task2", "p1", "foo", sname)

        (
            g1.manual_score,
            g2.manual_score,
            g3.manual_score,
            g4.manual_score) = (1, 2, 3, 4)
    a.db.commit()

    return a


def test_init(gradebook: Gradebook) -> None:
    assert gradebook.students == []
    assert gradebook.assignments == []


# Test students

def test_add_student(gradebook):
    s = gradebook.add_student('12345')
    assert s.id == '12345'
    assert gradebook.students == [s]

    # try adding a duplicate student
    with pytest.raises(InvalidEntry):
        gradebook.add_student('12345')

    # try adding a student with arguments
    s = gradebook.add_student('6789', last_name="Bar", first_name="Foo", email="foo@bar.com")
    assert s.id == '6789'
    assert s.last_name == "Bar"
    assert s.first_name == "Foo"
    assert s.email == "foo@bar.com"


def test_add_duplicate_student(gradebook):
    # we also need this test because this will cause an IntegrityError
    # under the hood rather than a FlushError
    gradebook.add_student('12345')
    with pytest.raises(InvalidEntry):
        gradebook.add_student('12345')


def test_find_student(gradebook):
    s1 = gradebook.add_student('12345')
    assert gradebook.find_student('12345') == s1

    s2 = gradebook.add_student('abcd')
    assert gradebook.find_student('12345') == s1
    assert gradebook.find_student('abcd') == s2


def test_find_nonexistant_student(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_student('12345')


def test_remove_student(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    assignment.remove_student('hacker123')

    with pytest.raises(MissingEntry):
        assignment.find_submission('foo', 'hacker123')
    with pytest.raises(MissingEntry):
        assignment.find_student('hacker123')


def test_update_or_create_student(gradebook):
    # first test creating it
    s1 = gradebook.update_or_create_student('hacker123')
    assert gradebook.find_student('hacker123') == s1
    assert s1.first_name is None

    # now test finding/updating it
    s2 = gradebook.update_or_create_student('hacker123', first_name='Alyssa')
    assert s1 == s2
    assert s2.first_name == 'Alyssa'


# Test assignments

def test_add_assignment(gradebook):
    a = gradebook.add_assignment('foo')
    assert a.name == 'foo'
    assert gradebook.assignments == [a]

    # try adding a duplicate assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_assignment('foo')

    # try adding an assignment with arguments
    now = datetime.utcnow()
    a = gradebook.add_assignment('bar', duedate=now)
    assert a.name == 'bar'
    assert a.duedate == now

    # try adding with a string timestamp
    a = gradebook.add_assignment('baz', duedate=now.isoformat())
    assert a.name == 'baz'
    assert a.duedate == now


def test_add_duplicate_assignment(gradebook):
    gradebook.add_assignment('foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_assignment('foo')


def test_find_assignment(gradebook):
    a1 = gradebook.add_assignment('foo')
    assert gradebook.find_assignment('foo') == a1

    a2 = gradebook.add_assignment('bar')
    assert gradebook.find_assignment('foo') == a1
    assert gradebook.find_assignment('bar') == a2


def test_find_nonexistant_assignment(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_assignment('foo')


def test_remove_assignment(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    notebooks = assignment.find_assignment('foo').notebooks
    grade_cells = [x for nb in notebooks for x in nb.grade_cells]
    solution_cells = [x for nb in notebooks for x in nb.solution_cells]
    source_cells = [x for nb in notebooks for x in nb.source_cells]

    assignment.remove_assignment('foo')

    for nb in notebooks:
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []
    for grade_cell in grade_cells:
        assert assignment.db.query(api.GradeCell).filter(api.GradeCell.id == grade_cell.id).all() == []
    for solution_cell in solution_cells:
        assert assignment.db.query(api.SolutionCell).filter(api.SolutionCell.id == solution_cell.id).all() == []
    for source_cell in source_cells:
        assert assignment.db.query(api.SourceCell).filter(api.SourceCell.id == source_cell.id).all() == []

    with pytest.raises(MissingEntry):
        assignment.find_assignment('foo')

    assert assignment.find_student('hacker123').submissions == []


def test_update_or_create_assignment(gradebook):
    # first test creating it
    a1 = gradebook.update_or_create_assignment('foo')
    assert gradebook.find_assignment('foo') == a1
    assert a1.duedate is None

    # now test finding/updating it
    a2 = gradebook.update_or_create_assignment('foo', duedate="2015-02-02 14:58:23.948203 America/Los_Angeles")
    assert a1 == a2
    assert a2.duedate == utils.parse_utc("2015-02-02 14:58:23.948203 America/Los_Angeles")

# Test notebooks


def test_add_notebook(gradebook):
    a = gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    assert n.name == 'p1'
    assert n.assignment == a
    assert a.notebooks == [n]

    # try adding a duplicate assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_notebook('p1', 'foo')


def test_add_duplicate_notebook(gradebook):
    # it should be ok to add a notebook with the same name, as long as
    # it's for different assignments
    gradebook.add_assignment('foo')
    gradebook.add_assignment('bar')
    n1 = gradebook.add_notebook('p1', 'foo')
    n2 = gradebook.add_notebook('p1', 'bar')
    assert n1.id != n2.id

    # but not ok to add a notebook with the same name for the same assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_notebook('p1', 'foo')


def test_find_notebook(gradebook):
    gradebook.add_assignment('foo')
    n1 = gradebook.add_notebook('p1', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1

    n2 = gradebook.add_notebook('p2', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1
    assert gradebook.find_notebook('p2', 'foo') == n2


def test_find_nonexistant_notebook(gradebook: Gradebook) -> None:
    # check that it doesn't find it when there is nothing in the db
    with pytest.raises(MissingEntry):
        gradebook.find_notebook('p1', 'foo')

    # check that it doesn't find it even if the assignment exists
    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_notebook('p1', 'foo')


def test_update_or_create_notebook(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    n1 = gradebook.update_or_create_notebook('p1', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1

    # now test finding/updating it
    n2 = gradebook.update_or_create_notebook('p1', 'foo')
    assert n1 == n2


def test_remove_notebook(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    notebooks = assignment.find_assignment('foo').notebooks

    for nb in notebooks:
        grade_cells = [x for x in nb.grade_cells]
        solution_cells = [x for x in nb.solution_cells]
        source_cells = [x for x in nb.source_cells]

        assignment.remove_notebook(nb.name, 'foo')
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []

        for grade_cell in grade_cells:
            assert assignment.db.query(api.GradeCell).filter(api.GradeCell.id == grade_cell.id).all() == []
        for solution_cell in solution_cells:
            assert assignment.db.query(api.SolutionCell).filter(api.SolutionCell.id == solution_cell.id).all() == []
        for source_cell in source_cells:
            assert assignment.db.query(api.SourceCell).filter(api.SourceCell.id == source_cell.id).all() == []

        with pytest.raises(MissingEntry):
            assignment.find_notebook(nb.name, 'foo')


def test_course_id_constructor():
    gb = api.Gradebook("sqlite:///:memory:")
    assert gb.db.query(api.Course).first().id == "default_course"

def test_course_id_multiple_assignments():
    course_one = "course-one"
    course_two = "course-two"

    gb_one = api.Gradebook("sqlite:///:memory:", course_id=course_one)
    gb_two = api.Gradebook("sqlite:///:memory:", course_id=course_two)

    assignment_one = gb_one.add_assignment('foo')
    assignent_two = gb_two.add_assignment('bar')

    assert assignment_one.course_id == course_one
    assert assignent_two.course_id == course_two

    assert len(gb_one.db.query(api.Course).all()) == 1
    assert gb_one.db.query(api.Course).first().id == course_one
    assert gb_one.db.query(api.Assignment).first().course_id == course_one
    assert gb_one.db.query(api.Assignment).first().course == gb_one.db.query(api.Course).first() 

    assert len(gb_two.db.query(api.Course).all()) == 1
    assert gb_two.db.query(api.Course).first().id == course_two
    assert gb_two.db.query(api.Assignment).first().course_id == course_two
    assert gb_two.db.query(api.Assignment).first().course == gb_two.db.query(api.Course).first()

# Test grade cells

def test_add_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
    assert gc.name == 'test1'
    assert gc.max_score == 2
    assert gc.cell_type == 'markdown'
    assert n.grade_cells == [gc]
    assert gc.notebook == n


def test_add_grade_cell_with_args(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_grade_cell(
        'test1', 'p1', 'foo',
        max_score=3, cell_type="code")
    assert gc.name == 'test1'
    assert gc.max_score == 3
    assert gc.cell_type == "code"


def test_create_invalid_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_grade_cell(
            'test1', 'p1', 'foo',
            max_score=3, cell_type="something")


def test_add_duplicate_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    with pytest.raises(InvalidEntry):
        gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')


def test_find_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1

    gc2 = gradebook.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='code')
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1
    assert gradebook.find_grade_cell('test2', 'p1', 'foo') == gc2


def test_find_nonexistant_grade_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')


def test_update_or_create_grade_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='code')
    assert gc1.max_score == 2
    assert gc1.cell_type == 'code'
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1

    # now test finding/updating it
    gc2 = gradebook.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=3)
    assert gc1 == gc2
    assert gc1.max_score == 3
    assert gc1.cell_type == 'code'


# Test solution cells

def test_add_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_solution_cell('test1', 'p1', 'foo')
    assert sc.name == 'test1'
    assert n.solution_cells == [sc]
    assert sc.notebook == n


def test_add_duplicate_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_solution_cell('test1', 'p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_solution_cell('test1', 'p1', 'foo')


def test_find_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.add_solution_cell('test1', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1

    sc2 = gradebook.add_solution_cell('test2', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1
    assert gradebook.find_solution_cell('test2', 'p1', 'foo') == sc2


def test_find_nonexistant_solution_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')


def test_update_or_create_solution_cell(gradebook: Gradebook) -> None:
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.update_or_create_solution_cell('test1', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1

    # now test finding/updating it
    sc2 = gradebook.update_or_create_solution_cell('test1', 'p1', 'foo')
    assert sc1 == sc2


# Test source cells

def test_add_source_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    assert sc.name == 'test1'
    assert sc.cell_type == 'code'
    assert n.source_cells == [sc]
    assert sc.notebook == n


def test_add_source_cell_with_args(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_source_cell(
        'test1', 'p1', 'foo',
        source="blah blah blah",
        cell_type="code", checksum="abcde")
    assert sc.name == 'test1'
    assert sc.source == "blah blah blah"
    assert sc.cell_type == "code"
    assert sc.checksum == "abcde"


def test_create_invalid_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_source_cell(
            'test1', 'p1', 'foo',
            source="blah blah blah",
            cell_type="something", checksum="abcde")


def test_add_duplicate_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    with pytest.raises(InvalidEntry):
        gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")


def test_find_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1

    sc2 = gradebook.add_source_cell('test2', 'p1', 'foo', cell_type="code")
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1
    assert gradebook.find_source_cell('test2', 'p1', 'foo') == sc2


def test_find_nonexistant_source_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')


def test_update_or_create_source_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.update_or_create_source_cell('test1', 'p1', 'foo', cell_type='code')
    assert sc1.cell_type == 'code'
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1

    # now test finding/updating it
    assert sc1.checksum is None
    sc2 = gradebook.update_or_create_source_cell('test1', 'p1', 'foo', checksum="123456")
    assert sc1 == sc2
    assert sc1.cell_type == 'code'
    assert sc1.checksum == "123456"


# Test submissions

def test_add_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')

    assert assignment.assignment_submissions('foo') == [s2, s1]
    assert assignment.student_submissions('hacker123') == [s1]
    assert assignment.student_submissions('bitdiddle') == [s2]
    assert assignment.find_submission('foo', 'hacker123') == s1
    assert assignment.find_submission('foo', 'bitdiddle') == s2


def test_add_duplicate_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')
    with pytest.raises(InvalidEntry):
        assignment.add_submission('foo', 'hacker123')


def test_remove_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    submission = assignment.find_submission('foo', 'hacker123')
    notebooks = submission.notebooks
    grades = [x for nb in notebooks for x in nb.grades]
    comments = [x for nb in notebooks for x in nb.comments]

    assignment.remove_submission('foo', 'hacker123')

    for nb in notebooks:
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []
    for grade in grades:
        assert assignment.db.query(api.Grade).filter(api.Grade.id == grade.id).all() == []
    for comment in comments:
        assert assignment.db.query(api.Comment).filter(api.Comment.id == comment.id).all() == []

    with pytest.raises(MissingEntry):
        assignment.find_submission('foo', 'hacker123')


def test_update_or_create_submission(assignment):
    assignment.add_student('hacker123')
    s1 = assignment.update_or_create_submission('foo', 'hacker123')
    assert s1.timestamp is None

    s2 = assignment.update_or_create_submission('foo', 'hacker123', timestamp="2015-02-02 14:58:23.948203 America/Los_Angeles")
    assert s1 == s2
    assert s2.timestamp == utils.parse_utc("2015-02-02 14:58:23.948203 America/Los_Angeles")


def test_find_submission_notebook(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks

    with pytest.raises(MissingEntry):
        assignment.find_submission_notebook('p2', 'foo', 'hacker123')

    n2 = assignment.find_submission_notebook('p1', 'foo', 'hacker123')
    assert n1 == n2


def test_find_submission_notebook_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks

    with pytest.raises(MissingEntry):
        assignment.find_submission_notebook_by_id('12345')

    n2 = assignment.find_submission_notebook_by_id(n1.id)
    assert n1 == n2


def test_remove_submission_notebook(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    submission = assignment.find_submission('foo', 'hacker123')
    notebooks = submission.notebooks

    for nb in notebooks:
        grades = [x for x in nb.grades]
        comments = [x for x in nb.comments]

        assignment.remove_submission_notebook(nb.name, 'foo', 'hacker123')
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []

        for grade in grades:
            assert assignment.db.query(api.Grade).filter(api.Grade.id == grade.id).all() == []
        for comment in comments:
            assert assignment.db.query(api.Comment).filter(api.Comment.id == comment.id).all() == []

        with pytest.raises(MissingEntry):
            assignment.find_submission_notebook(nb.name, 'foo', 'hacker123')


def test_find_grade(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    grades = n1.grades

    for g1 in grades:
        g2 = assignment.find_grade(g1.name, 'p1', 'foo', 'hacker123')
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_grade('asdf', 'p1', 'foo', 'hacker123')


def test_find_grade_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    grades = n1.grades

    for g1 in grades:
        g2 = assignment.find_grade_by_id(g1.id)
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_grade_by_id('12345')


def test_find_comment(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    comments = n1.comments

    for c1 in comments:
        c2 = assignment.find_comment(c1.name, 'p1', 'foo', 'hacker123')
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_comment('asdf', 'p1', 'foo', 'hacker123')


def test_find_comment_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    comments = n1.comments

    for c1 in comments:
        c2 = assignment.find_comment_by_id(c1.id)
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_comment_by_id('12345')


# Test average scores

def test_average_assignment_score(assignment):
    assert assignment.average_assignment_score('foo') == 0.0
    assert assignment.average_assignment_code_score('foo') == 0.0
    assert assignment.average_assignment_written_score('foo') == 0.0

    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    assert assignment.average_assignment_score('foo') == 0.0
    assert assignment.average_assignment_code_score('foo') == 0.0
    assert assignment.average_assignment_written_score('foo') == 0.0

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    assert assignment.average_assignment_score('foo') == 2.25
    assert assignment.average_assignment_code_score('foo') == 0.75
    assert assignment.average_assignment_written_score('foo') == 1.5


def test_average_notebook_score(assignment: Gradebook) -> None:
    assert assignment.average_notebook_score('p1', 'foo') == 0
    assert assignment.average_notebook_code_score('p1', 'foo') == 0
    assert assignment.average_notebook_written_score('p1', 'foo') == 0

    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    assert assignment.average_notebook_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_code_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_written_score('p1', 'foo') == 0.0

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    assert assignment.average_notebook_score('p1', 'foo') == 2.25
    assert assignment.average_notebook_code_score('p1', 'foo') == 0.75
    assert assignment.average_notebook_written_score('p1', 'foo') == 1.5


# Test mass dictionary queries

def test_student_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_student('louisreasoner')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    students = assignment.student_dicts()
    a = sorted(students, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assignment.students], key=lambda x: x["id"])
    assert a == b


def test_student_dicts_zero_points(gradebook):
    gradebook.add_assignment("ps1")
    s = gradebook.add_student("1234")
    assert gradebook.student_dicts() == [s.to_dict()]


def test_notebook_submission_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')
    s1.flagged = True
    s2.flagged = False

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    notebook = assignment.find_notebook("p1", "foo")
    submissions = assignment.notebook_submission_dicts("p1", "foo")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_submission_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')
    s1.flagged = True
    s2.flagged = False

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    a = sorted(assignment.submission_dicts("foo"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assignment.find_assignment("foo").submissions], key=lambda x: x["id"])
    assert a == b


def test_grant_extension(gradebook):
    gradebook.add_assignment("ps1", duedate="2018-05-09 10:00:00")
    gradebook.add_student("hacker123")
    s1 = gradebook.add_submission("ps1", "hacker123")
    assert s1.extension is None
    assert s1.duedate == datetime(2018, 5, 9, 10, 0, 0)

    gradebook.grant_extension('ps1', 'hacker123', minutes=10)
    assert s1.extension == timedelta(minutes=10)
    assert s1.duedate == datetime(2018, 5, 9, 10, 10, 0)

    gradebook.grant_extension('ps1', 'hacker123', hours=1)
    assert s1.extension == timedelta(hours=1)
    assert s1.duedate == datetime(2018, 5, 9, 11, 0, 0)

    gradebook.grant_extension('ps1', 'hacker123', days=2)
    assert s1.extension == timedelta(days=2)
    assert s1.duedate == datetime(2018, 5, 11, 10, 0, 0)

    gradebook.grant_extension('ps1', 'hacker123', weeks=3)
    assert s1.extension == timedelta(weeks=3)
    assert s1.duedate == datetime(2018, 5, 30, 10, 0, 0)

    gradebook.grant_extension('ps1', 'hacker123')
    assert s1.extension is None
    assert s1.duedate == datetime(2018, 5, 9, 10, 0, 0)


# Test task cells

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
    gc2 = gradebook.update_or_create_grade_cell('test2', 'p2', 'foo2', max_score=2, cell_type='code')
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
    # assert gc2.max_score == 5
    n1 = gradebook.find_notebook('p1', 'foo')
    assert n1.max_score_gradecell == 35
    assert n1.max_score_taskcell == 4000
    assert n1.max_score == 4035


def test_grades_include_taskcells(assignmentWithSubmissionWithMarks: Gradebook) -> None:
    s = assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        grades = n.grades
        assert len(grades) == 6


# next 4 same as in normal tests, but with an assignment with tasks
def test_find_grade(assignmentWithSubmissionWithMarks):
    s = assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        grades = n.grades
        for g1 in grades:
            g2 = assignmentWithSubmissionWithMarks.find_grade(g1.name, n.name, 'foo', 'hacker123')
            assert g1 == g2

    with pytest.raises(MissingEntry):
        assignmentWithSubmissionWithMarks.find_grade('asdf', 'p1', 'foo', 'hacker123')


def test_find_grade_by_id(assignmentWithSubmissionWithMarks):
    s = assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        grades = n.grades

        for g1 in grades:
            g2 = assignmentWithSubmissionWithMarks.find_grade_by_id(g1.id)
            assert g1 == g2

        with pytest.raises(MissingEntry):
            assignmentWithSubmissionWithMarks.find_grade_by_id('12345')


def test_find_comment(assignmentWithSubmissionWithMarks: Gradebook) -> None:
    s = assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        comments = n.comments

        for c1 in comments:
            c2 = assignmentWithSubmissionWithMarks.find_comment(c1.name, n.name, 'foo', 'hacker123')
            assert c1 == c2

        with pytest.raises(MissingEntry):
            assignmentWithSubmissionWithMarks.find_comment('asdf', n.name, 'foo', 'hacker123')


def test_find_comment_by_id(assignmentWithSubmissionWithMarks):
    s = assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        comments = n.comments

        for c1 in comments:
            c2 = assignmentWithSubmissionWithMarks.find_comment_by_id(c1.id)
            assert c1 == c2

        with pytest.raises(MissingEntry):
            assignmentWithSubmissionWithMarks.find_comment_by_id('12345')


def test_average_assignment_score_empty(assignment):
    assert assignment.average_assignment_score('foo') == 0.0
    assert assignment.average_assignment_code_score('foo') == 0.0
    assert assignment.average_assignment_written_score('foo') == 0.0
    assert assignment.average_assignment_task_score('foo') == 0.0


def test_average_assignment_no_score(assignmentWithSubmissionNoMarks):
    assert assignmentWithSubmissionNoMarks.average_assignment_score('foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_assignment_code_score('foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_assignment_written_score('foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_assignment_task_score('foo') == 0.0


def test_average_assignment_with_score(assignmentWithSubmissionWithMarks):
    assert assignmentWithSubmissionWithMarks.average_assignment_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades) / 2.0
    assert assignmentWithSubmissionWithMarks.average_assignment_code_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_code) / 2.0
    assert assignmentWithSubmissionWithMarks.average_assignment_written_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_written) / 2.0
    assert assignmentWithSubmissionWithMarks.average_assignment_task_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_task) / 2.0


def test_average_notebook_score_empty(assignment):
    assert assignment.average_notebook_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_code_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_written_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_task_score('p1', 'foo') == 0.0


def test_average_notebook_no_score(assignmentWithSubmissionNoMarks):
    assert assignmentWithSubmissionNoMarks.average_notebook_score('p1', 'foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_code_score('p1', 'foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_written_score('p1', 'foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_task_score('p1', 'foo') == 0.0


def test_average_notebook_with_score(assignmentWithSubmissionWithMarks: Gradebook) -> None:
    assert assignmentWithSubmissionWithMarks.average_notebook_score('p1', 'foo') == sum(assignmentWithSubmissionWithMarks.usedgrades) / 2.0
    assert assignmentWithSubmissionWithMarks.average_notebook_code_score('p1', 'foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_code) / 2.0
    assert assignmentWithSubmissionWithMarks.average_notebook_written_score('p1', 'foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_written) / 2.0
    assert assignmentWithSubmissionWithMarks.average_notebook_task_score('p1', 'foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_task) / 2.0


def test_student_dicts(assignmentWithSubmissionWithMarks):
    assign = assignmentWithSubmissionWithMarks
    students = assign.student_dicts()
    a = sorted(students, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.students], key=lambda x: x["id"])
    assert a == b


def test_notebook_max_score(assignmentManyStudents):
    assign = assignmentManyStudents
    notebook = assign.find_notebook("p1", "foo")
    assert notebook.max_score == 44


def test_notebook_max_score_multiple_notebooks(FiveNotebooks):
    assign = FiveNotebooks
    notebook = assign.find_notebook("n1", "a1")
    assert notebook.max_score == 555


def test_submission_max_score(assignmentManyStudents):
    assign = assignmentManyStudents
    s = assign.find_submission('foo', 's1')
    assert s.max_score == 88
    for n in s.notebooks:
        assert n.max_score == 44


def test_submission_max_score_multiple_notebooks(FiveNotebooks):
    assign = FiveNotebooks
    s = assign.find_submission('a1', 's1')
    assert s.max_score == 5 * 555
    for n in s.notebooks:
        assert n.max_score == 555


def test_notebook_submission_dicts_multiple_students(FiveStudents):
    assign = FiveStudents
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_notebook_submission_dicts_multiple_notebooks(FiveNotebooks):
    assign = FiveNotebooks
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_notebook_submission_dicts_multiple_assignments(FiveAssignments):
    assign = FiveAssignments
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_notebook_submission_dicts(assignmentWithSubmissionWithMarks):
    assign = assignmentWithSubmissionWithMarks
    notebook = assign.find_notebook("p1", "foo")
    submissions = assign.notebook_submission_dicts("p1", "foo")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_submission_dicts_multiple_students(FiveStudents):
    assign = FiveStudents
    a = sorted(assign.submission_dicts("a1"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.find_assignment("a1").submissions], key=lambda x: x["id"])
    assert a == b


def test_submission_dicts_multiple_notebooks(FiveNotebooks):
    assign = FiveNotebooks
    a = sorted(assign.submission_dicts("a1"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.find_assignment("a1").submissions], key=lambda x: x["id"])
    assert a == b
