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

def makeAssignments(gb,na,nn,ns,grades=[1,2,10,20,100,200]):
    for si in range(ns):
        sname="s{0}".format(si+1)
        gb.add_student(sname)
    for ia in range(na):
        aname='a{0}'.format(ia+1)
        a=gb.add_assignment(aname)
        for ni in range(nn):
            nname='n{0}'.format(ni+1)
            n=gb.add_notebook(nname, aname)
            gb.add_solution_cell('solution1', nname, aname)
            gb.add_solution_cell('solution2', nname, aname)
            gb.add_source_cell('source1', nname, aname, cell_type='code')
            gb.add_source_cell('source2', nname, aname, cell_type='markdown')
            gb.add_source_cell('solution1', nname, aname, cell_type='code')
            gb.add_grade_cell('grade_code1', nname, aname, cell_type='code',max_score=2)
            gb.add_grade_cell('grade_code2', nname, aname, cell_type='code', max_score=3)
            gb.add_grade_cell('grade_written1', nname, aname, cell_type='markdown',max_score=20)
            gb.add_grade_cell('grade_written2', nname, aname, cell_type='markdown', max_score=30)
            gb.add_task_cell('task1', nname, aname, cell_type='markdown',max_score=200)
            gb.add_task_cell('task2', nname, aname, cell_type='markdown', max_score=300)
        for si in range(ns):
            sname="s{0}".format(si+1)
            sub=gb.add_submission(aname, sname)
            sub.flagged=False
            for ni in range(nn):
                nname='n{0}'.format(ni+1)    
            
                g1 = gb.find_grade("grade_code1", nname, aname, sname)
                g2 = gb.find_grade("grade_code2", nname, aname, sname)
                g3 = gb.find_grade("grade_written1", nname, aname, sname)
                g4 = gb.find_grade("grade_written2", nname, aname, sname)
                g5 = gb.find_grade("task1", nname, aname, sname)
                g6 = gb.find_grade("task2", nname, aname, sname)

                (g1.manual_score , g2.manual_score , g3.manual_score , g4.manual_score,
                 g5.manual_score , g6.manual_score 
                ) = grades
            gb.db.commit()

    return gb


@pytest.fixture
def FiveStudents(gradebook):
    return makeAssignments(gradebook,1,1,5)

@pytest.fixture
def FiveNotebooks(gradebook):
    return makeAssignments(gradebook,1,5,1)
@pytest.fixture
def FiveAssignments(gradebook):
    return makeAssignments(gradebook,5,1,1)


@pytest.fixture
def assignment(gradebook):
    for f in ['foo','foo2']:
        gradebook.add_assignment(f)
        for n in ['p1','p2']:
            gradebook.add_notebook(n, f)
            gradebook.add_solution_cell('solution1', n, f)
            gradebook.add_solution_cell('test2', n, f)
            gradebook.add_source_cell('test1', n, f, cell_type='code')
            gradebook.add_source_cell('test2', n, f, cell_type='markdown')
            gradebook.add_source_cell('solution1', n, f, cell_type='code')
            gradebook.add_grade_cell('grade_code1', n, f, cell_type='code',max_score=1)
            gradebook.add_grade_cell('grade_code2', n, f, cell_type='code', max_score=10)
            gradebook.add_grade_cell('grade_written1', n, f, cell_type='markdown',max_score=1)
            gradebook.add_grade_cell('grade_written2', n, f, cell_type='markdown', max_score=10)
            gradebook.add_task_cell('task1', n, f, cell_type='markdown',max_score=2)
            gradebook.add_task_cell('task2', n, f, cell_type='markdown', max_score=20)

    return gradebook

@pytest.fixture
def assignmentWithSubmissionNoMarks(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_student('louisreasoner')
    s1=assignment.add_submission('foo', 'hacker123')
    s2=assignment.add_submission('foo', 'bitdiddle')
    s1.flagged=True
    s2.flagged=False
    assignment.db.commit()
    return assignment

possiblegrades=[
    [0.5,2,3,5,1,7,2,1],
    [0.1,4,0.25,1,7,0.0,1,1],
    [0]*8,
    [2]*8,
    [0.25]*8,
]

@pytest.fixture(params=possiblegrades)
def assignmentWithSubmissionWithMarks(assignmentWithSubmissionNoMarks,request):
    a=assignmentWithSubmissionNoMarks
    g1 = a.find_grade("grade_code1", "p1", "foo", "bitdiddle")
    g2 = a.find_grade("grade_code2", "p1", "foo", "bitdiddle")

    g3 = a.find_grade("grade_written1", "p1", "foo", "hacker123")
    g4 = a.find_grade("grade_written2", "p1", "foo", "hacker123")

    g5 = a.find_grade("task1", "p1", "foo", "bitdiddle")
    g6 = a.find_grade("task2", "p1", "foo", "bitdiddle")
    g7 = a.find_grade("task1", "p1", "foo", "hacker123")
    g8 = a.find_grade("task2", "p1", "foo", "hacker123")

    (g1.manual_score , g2.manual_score , g3.manual_score , g4.manual_score , g5.manual_score ,
     g6.manual_score , g7.manual_score , g8.manual_score      
     ) = request.param
    a.db.commit()
    a.usedgrades = request.param
    a.usedgrades_code = request.param[:2]
    a.usedgrades_written = request.param[2:4]
    a.usedgrades_task = request.param[4:]

    return a

@pytest.fixture
def assignmentManyStudents(assignment,request):
    a=assignment
    for s in range(50):
        sname='s{0}'.format(s)
        a.add_student(sname)
        sub=a.add_submission('foo', sname)
        g1 = a.find_grade("grade_code1", "p1", "foo", sname)
        g2 = a.find_grade("grade_written1", "p1", "foo", sname)
        g3 = a.find_grade("task1", "p1", "foo", sname)
        g4 = a.find_grade("task2", "p1", "foo", sname)

        (
            g1.manual_score , 
            g2.manual_score , 
            g3.manual_score , 
            g4.manual_score ) = (1,2,3,4)    
    a.db.commit()

    return a

@pytest.fixture
def assignmentTwoStudents(assignment,request):
    a=assignment
    for s in range(50):
        sname='s{0}'.format(s)
        a.add_student(sname)
        sub=a.add_submission('foo', sname)
        g1 = a.find_grade("grade_code1", "p1", "foo", sname)
        g2 = a.find_grade("grade_written1", "p1", "foo", sname)
        g3 = a.find_grade("task1", "p1", "foo", sname)
        g4 = a.find_grade("task2", "p1", "foo", sname)

        (
            g1.manual_score , 
            g2.manual_score , 
            g3.manual_score , 
            g4.manual_score ) = (1,2,3,4)    
    a.db.commit()

    return a


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
    #assert gc2.max_score == 5
    n1=gradebook.find_notebook('p1','foo')
    assert n1.max_score_gradecell == 35
    assert n1.max_score_taskcell == 4000
    assert n1.max_score == 4035


def test_grades_include_taskcells(assignmentWithSubmissionWithMarks):
    s=assignmentWithSubmissionWithMarks.find_submission('foo', 'hacker123')
    for n in s.notebooks:
        grades = n.grades
        assert  len(grades)==6

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
    for n in  s.notebooks:
        grades = n.grades

        for g1 in grades:
            g2 = assignmentWithSubmissionWithMarks.find_grade_by_id(g1.id)
            assert g1 == g2

        with pytest.raises(MissingEntry):
            assignmentWithSubmissionWithMarks.find_grade_by_id('12345')

def test_find_comment(assignmentWithSubmissionWithMarks):
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
    assert assignmentWithSubmissionWithMarks.average_assignment_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades)/2.0 
    assert assignmentWithSubmissionWithMarks.average_assignment_code_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_code)/2.0 
    assert assignmentWithSubmissionWithMarks.average_assignment_written_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_written)/2.0 
    assert assignmentWithSubmissionWithMarks.average_assignment_task_score('foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_task)/2.0 


def test_average_notebook_score_empty(assignment):
    assert assignment.average_notebook_score('p1','foo') == 0.0
    assert assignment.average_notebook_code_score('p1','foo') == 0.0
    assert assignment.average_notebook_written_score('p1','foo') == 0.0
    assert assignment.average_notebook_task_score('p1','foo') == 0.0



def test_average_notebook_no_score(assignmentWithSubmissionNoMarks):

    assert assignmentWithSubmissionNoMarks.average_notebook_score('p1','foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_code_score('p1','foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_written_score('p1','foo') == 0.0
    assert assignmentWithSubmissionNoMarks.average_notebook_task_score('p1','foo') == 0.0

def test_average_notebook_with_score(assignmentWithSubmissionWithMarks):
    assert assignmentWithSubmissionWithMarks.average_notebook_score('p1','foo') == sum(assignmentWithSubmissionWithMarks.usedgrades)/2 
    assert assignmentWithSubmissionWithMarks.average_notebook_code_score('p1','foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_code)/2 
    assert assignmentWithSubmissionWithMarks.average_notebook_written_score('p1','foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_written)/2 
    assert assignmentWithSubmissionWithMarks.average_notebook_task_score('p1','foo') == sum(assignmentWithSubmissionWithMarks.usedgrades_task)/2 



def test_student_dicts(assignmentWithSubmissionWithMarks):
    assign=assignmentWithSubmissionWithMarks
    students = assign.student_dicts()
    a = sorted(students, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.students], key=lambda x: x["id"])
    assert a == b

def test_notebook_max_score(assignmentManyStudents):
    assign=assignmentManyStudents
    notebook = assign.find_notebook("p1", "foo")
    assert notebook.max_score == 44

def test_notebook_max_score_multiple_notebooks(FiveNotebooks):
    assign=FiveNotebooks
    notebook = assign.find_notebook("n1", "a1")
    assert notebook.max_score == 555

def test_submission_max_score(assignmentManyStudents):
    assign=assignmentManyStudents
    s = assign.find_submission('foo', 's1')
    assert s.max_score == 88
    for n in s.notebooks:
        assert n.max_score == 44

def test_submission_max_score_multiple_notebooks(FiveNotebooks):
    assign=FiveNotebooks
    s = assign.find_submission('a1', 's1')
    assert s.max_score == 5*555
    for n in s.notebooks:
        assert n.max_score == 555


def test_notebook_submission_dicts_multiple_students(FiveStudents):
    assign=FiveStudents
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b

def test_notebook_submission_dicts_multiple_notebooks(FiveNotebooks):
    assign=FiveNotebooks
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b

def test_notebook_submission_dicts_multiple_assignments(FiveAssignments):
    assign=FiveAssignments
    notebook = assign.find_notebook("n1", "a1")
    submissions = assign.notebook_submission_dicts("n1", "a1")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_notebook_submission_dicts(assignmentWithSubmissionWithMarks):
    assign=assignmentWithSubmissionWithMarks
    notebook = assign.find_notebook("p1", "foo")
    submissions = assign.notebook_submission_dicts("p1", "foo")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b

def test_submission_dicts_multiple_students(FiveStudents):
    assign=FiveStudents
    a = sorted(assign.submission_dicts("a1"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.find_assignment("a1").submissions], key=lambda x: x["id"])
    assert a == b

def test_submission_dicts_multiple_notebooks(FiveNotebooks):
    assign=FiveNotebooks
    a = sorted(assign.submission_dicts("a1"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assign.find_assignment("a1").submissions], key=lambda x: x["id"])
    assert a == b
