import pytest

from datetime import datetime
from nbgrader import api
from nbgrader.api import InvalidEntry, MissingEntry

class TestGradebook(object):

    def setup(self):
        self.gb = api.Gradebook("sqlite:///:memory:")

    def teardown(self):
        self.gb.db.close()

    def test_init(self):
        assert self.gb.students == []
        assert self.gb.assignments == []

    #### Test students

    def test_add_student(self):
        s = self.gb.add_student('12345')
        assert s.id == '12345'
        assert self.gb.students == [s]

        # try adding a duplicate student
        with pytest.raises(InvalidEntry):
            self.gb.add_student('12345')

        # try adding a student with arguments
        s = self.gb.add_student('6789', last_name="Bar", first_name="Foo", email="foo@bar.com")
        assert s.id == '6789'
        assert s.last_name == "Bar"
        assert s.first_name == "Foo"
        assert s.email == "foo@bar.com"

    def test_add_duplicate_student(self):
        # we also need this test because this will cause an IntegrityError
        # under the hood rather than a FlushError
        self.gb.add_student('12345')
        with pytest.raises(InvalidEntry):
            self.gb.add_student('12345')

    def test_find_student(self):
        s1 = self.gb.add_student('12345')
        assert self.gb.find_student('12345') == s1

        s2 = self.gb.add_student('abcd')
        assert self.gb.find_student('12345') == s1
        assert self.gb.find_student('abcd') == s2

    def test_find_nonexistant_student(self):
        with pytest.raises(MissingEntry):
            self.gb.find_student('12345')

    #### Test assignments

    def test_add_assignment(self):
        a = self.gb.add_assignment('foo')
        assert a.name == 'foo'
        assert self.gb.assignments == [a]

        # try adding a duplicate assignment
        with pytest.raises(InvalidEntry):
            self.gb.add_assignment('foo')

        # try adding an assignment with arguments
        now = datetime.now()
        a = self.gb.add_assignment('bar', duedate=now)
        assert a.name == 'bar'
        assert a.duedate == now

        # try adding with a string timestamp
        a = self.gb.add_assignment('baz', duedate=now.isoformat())
        assert a.name == 'baz'
        assert a.duedate == now

    def test_add_duplicate_assignment(self):
        self.gb.add_assignment('foo')
        with pytest.raises(InvalidEntry):
            self.gb.add_assignment('foo')

    def test_find_assignment(self):
        a1 = self.gb.add_assignment('foo')
        assert self.gb.find_assignment('foo') == a1

        a2 = self.gb.add_assignment('bar')
        assert self.gb.find_assignment('foo') == a1
        assert self.gb.find_assignment('bar') == a2

    def test_find_nonexistant_assignment(self):
        with pytest.raises(MissingEntry):
            self.gb.find_assignment('foo')

    #### Test notebooks

    def test_add_notebook(self):
        a = self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        assert n.name == 'p1'
        assert n.assignment == a
        assert a.notebooks == [n]

        # try adding a duplicate assignment
        with pytest.raises(InvalidEntry):
            self.gb.add_notebook('p1', 'foo')

    def test_add_duplicate_notebook(self):
        # it should be ok to add a notebook with the same name, as long as
        # it's for different assignments
        self.gb.add_assignment('foo')
        self.gb.add_assignment('bar')
        n1 = self.gb.add_notebook('p1', 'foo')
        n2 = self.gb.add_notebook('p1', 'bar')
        assert n1.id != n2.id

        # but not ok to add a notebook with the same name for the same assignment
        with pytest.raises(InvalidEntry):
            self.gb.add_notebook('p1', 'foo')

    def test_find_notebook(self):
        self.gb.add_assignment('foo')
        n1 = self.gb.add_notebook('p1', 'foo')
        assert self.gb.find_notebook('p1', 'foo') == n1

        n2 = self.gb.add_notebook('p2', 'foo')
        assert self.gb.find_notebook('p1', 'foo') == n1
        assert self.gb.find_notebook('p2', 'foo') == n2

    def test_find_nonexistant_notebook(self):
        # check that it doesn't find it when there is nothing in the db
        with pytest.raises(MissingEntry):
            self.gb.find_notebook('p1', 'foo')

        # check that it doesn't find it even if the assignment exists
        self.gb.add_assignment('foo')
        with pytest.raises(MissingEntry):
            self.gb.find_notebook('p1', 'foo')

    def test_update_or_create_notebook(self):
        # first test creating it
        self.gb.add_assignment('foo')
        n1 = self.gb.update_or_create_notebook('p1', 'foo')
        assert self.gb.find_notebook('p1', 'foo') == n1

        # now test finding/updating it
        n2 = self.gb.update_or_create_notebook('p1', 'foo')
        assert n1 == n2

    #### Test grade cells

    def test_add_grade_cell(self):
        self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        gc = self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
        assert gc.name == 'test1'
        assert gc.max_score == 2
        assert gc.cell_type == 'markdown'
        assert n.grade_cells == [gc]
        assert gc.notebook == n

    def test_add_grade_cell_with_args(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc = self.gb.add_grade_cell(
            'test1', 'p1', 'foo',
            max_score=3, source="blah blah blah",
            cell_type="code", checksum="abcde")
        assert gc.name == 'test1'
        assert gc.max_score == 3
        assert gc.source == "blah blah blah"
        assert gc.cell_type == "code"
        assert gc.checksum == "abcde"

    def test_create_invalid_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        with pytest.raises(InvalidEntry):
            self.gb.add_grade_cell(
                'test1', 'p1', 'foo',
                max_score=3, source="blah blah blah",
                cell_type="something", checksum="abcde")

    def test_add_duplicate_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
        with pytest.raises(InvalidEntry):
            self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')

    def test_find_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc1 = self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
        assert self.gb.find_grade_cell('test1', 'p1', 'foo') == gc1

        gc2 = self.gb.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='code')
        assert self.gb.find_grade_cell('test1', 'p1', 'foo') == gc1
        assert self.gb.find_grade_cell('test2', 'p1', 'foo') == gc2

    def test_find_nonexistant_grade_cell(self):
        with pytest.raises(MissingEntry):
            self.gb.find_grade_cell('test1', 'p1', 'foo')

        self.gb.add_assignment('foo')
        with pytest.raises(MissingEntry):
            self.gb.find_grade_cell('test1', 'p1', 'foo')

        self.gb.add_notebook('p1', 'foo')
        with pytest.raises(MissingEntry):
            self.gb.find_grade_cell('test1', 'p1', 'foo')

    def test_update_or_create_grade_cell(self):
        # first test creating it
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc1 = self.gb.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='code')
        assert gc1.max_score == 2
        assert gc1.cell_type == 'code'
        assert self.gb.find_grade_cell('test1', 'p1', 'foo') == gc1

        # now test finding/updating it
        assert gc1.checksum == None
        gc2 = self.gb.update_or_create_grade_cell('test1', 'p1', 'foo', checksum="123456")
        assert gc1 == gc2
        assert gc1.max_score == 2
        assert gc1.cell_type == 'code'
        assert gc1.checksum == "123456"

    #### Test solution cells

    def test_add_solution_cell(self):
        self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        sc = self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        assert sc.name == 'test1'
        assert sc.cell_type == 'code'
        assert n.solution_cells == [sc]
        assert sc.notebook == n

    def test_add_solution_cell_with_args(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc = self.gb.add_solution_cell(
            'test1', 'p1', 'foo',
            source="blah blah blah",
            cell_type="code", checksum="abcde")
        assert sc.name == 'test1'
        assert sc.source == "blah blah blah"
        assert sc.cell_type == "code"
        assert sc.checksum == "abcde"

    def test_create_invalid_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        with pytest.raises(InvalidEntry):
            self.gb.add_solution_cell(
                'test1', 'p1', 'foo',
                source="blah blah blah",
                cell_type="something", checksum="abcde")

    def test_add_duplicate_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        with pytest.raises(InvalidEntry):
            self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")

    def test_find_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc1 = self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        assert self.gb.find_solution_cell('test1', 'p1', 'foo') == sc1

        sc2 = self.gb.add_solution_cell('test2', 'p1', 'foo', cell_type="code")
        assert self.gb.find_solution_cell('test1', 'p1', 'foo') == sc1
        assert self.gb.find_solution_cell('test2', 'p1', 'foo') == sc2

    def test_find_nonexistant_solution_cell(self):
        with pytest.raises(MissingEntry):
            self.gb.find_solution_cell('test1', 'p1', 'foo')

        self.gb.add_assignment('foo')
        with pytest.raises(MissingEntry):
            self.gb.find_solution_cell('test1', 'p1', 'foo')

        self.gb.add_notebook('p1', 'foo')
        with pytest.raises(MissingEntry):
            self.gb.find_solution_cell('test1', 'p1', 'foo')

    def test_update_or_create_solution_cell(self):
        # first test creating it
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc1 = self.gb.update_or_create_solution_cell('test1', 'p1', 'foo', cell_type='code')
        assert sc1.cell_type == 'code'
        assert self.gb.find_solution_cell('test1', 'p1', 'foo') == sc1

        # now test finding/updating it
        assert sc1.checksum == None
        sc2 = self.gb.update_or_create_solution_cell('test1', 'p1', 'foo', checksum="123456")
        assert sc1 == sc2
        assert sc1.cell_type == 'code'
        assert sc1.checksum == "123456"

    #### Test submissions

    def _add_assignment(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
        self.gb.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='markdown')
        self.gb.add_solution_cell('solution1', 'p1', 'foo', cell_type='code')
        self.gb.add_solution_cell('test2', 'p1', 'foo', cell_type='markdown')

    def test_add_submission(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_student('bitdiddle')
        s1 = self.gb.add_submission('foo', 'hacker123')
        s2 = self.gb.add_submission('foo', 'bitdiddle')

        assert self.gb.assignment_submissions('foo') == [s2, s1]
        assert self.gb.student_submissions('hacker123') == [s1]
        assert self.gb.student_submissions('bitdiddle') == [s2]
        assert self.gb.find_submission('foo', 'hacker123') == s1
        assert self.gb.find_submission('foo', 'bitdiddle') == s2

    def test_add_duplicate_submission(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_submission('foo', 'hacker123')
        with pytest.raises(InvalidEntry):
            self.gb.add_submission('foo', 'hacker123')

    ### Test average scores

    def test_average_assignment_score(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_student('bitdiddle')
        self.gb.add_submission('foo', 'hacker123')
        self.gb.add_submission('foo', 'bitdiddle')

        assert self.gb.average_assignment_score('foo') == 0.0
        assert self.gb.average_assignment_code_score('foo') == 0.0
        assert self.gb.average_assignment_written_score('foo') == 0.0

        g1 = self.gb.find_grade("test1", "p1", "foo", "hacker123")
        g2 = self.gb.find_grade("test2", "p1", "foo", "hacker123")
        g3 = self.gb.find_grade("test1", "p1", "foo", "bitdiddle")
        g4 = self.gb.find_grade("test2", "p1", "foo", "bitdiddle")

        g1.manual_score = 0.5
        g2.manual_score = 2
        g3.manual_score = 1
        g4.manual_score = 1
        self.gb.db.commit()

        assert self.gb.average_assignment_score('foo') == 2.25
        assert self.gb.average_assignment_code_score('foo') == 0.75
        assert self.gb.average_assignment_written_score('foo') == 1.5

    def test_average_notebook_score(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_student('bitdiddle')
        self.gb.add_submission('foo', 'hacker123')
        self.gb.add_submission('foo', 'bitdiddle')

        assert self.gb.average_notebook_score('p1', 'foo') == 0.0
        assert self.gb.average_notebook_code_score('p1', 'foo') == 0.0
        assert self.gb.average_notebook_written_score('p1', 'foo') == 0.0

        g1 = self.gb.find_grade("test1", "p1", "foo", "hacker123")
        g2 = self.gb.find_grade("test2", "p1", "foo", "hacker123")
        g3 = self.gb.find_grade("test1", "p1", "foo", "bitdiddle")
        g4 = self.gb.find_grade("test2", "p1", "foo", "bitdiddle")

        g1.manual_score = 0.5
        g2.manual_score = 2
        g3.manual_score = 1
        g4.manual_score = 1
        self.gb.db.commit()

        assert self.gb.average_notebook_score('p1', 'foo') == 2.25
        assert self.gb.average_notebook_code_score('p1', 'foo') == 0.75
        assert self.gb.average_notebook_written_score('p1', 'foo') == 1.5

    ## Test mass dictionary queries

    def test_student_dicts(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_student('bitdiddle')
        self.gb.add_submission('foo', 'hacker123')
        self.gb.add_submission('foo', 'bitdiddle')

        g1 = self.gb.find_grade("test1", "p1", "foo", "hacker123")
        g2 = self.gb.find_grade("test2", "p1", "foo", "hacker123")
        g3 = self.gb.find_grade("test1", "p1", "foo", "bitdiddle")
        g4 = self.gb.find_grade("test2", "p1", "foo", "bitdiddle")

        g1.manual_score = 0.5
        g2.manual_score = 2
        g3.manual_score = 1
        g4.manual_score = 1
        self.gb.db.commit()

        students = self.gb.student_dicts()
        a = sorted(students, key=lambda x: x["id"])
        b = sorted([x.to_dict() for x in self.gb.students], key=lambda x: x["id"])
        assert a == b

    def test_notebook_submission_dicts(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_student('bitdiddle')
        self.gb.add_submission('foo', 'hacker123')
        self.gb.add_submission('foo', 'bitdiddle')

        g1 = self.gb.find_grade("test1", "p1", "foo", "hacker123")
        g2 = self.gb.find_grade("test2", "p1", "foo", "hacker123")
        g3 = self.gb.find_grade("test1", "p1", "foo", "bitdiddle")
        g4 = self.gb.find_grade("test2", "p1", "foo", "bitdiddle")

        g1.manual_score = 0.5
        g2.manual_score = 2
        g3.manual_score = 1
        g4.manual_score = 1
        self.gb.db.commit()

        notebook = self.gb.find_notebook("p1", "foo")
        submissions = self.gb.notebook_submission_dicts("p1", "foo")
        a = sorted(submissions, key=lambda x: x["id"])
        b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
        assert a == b

