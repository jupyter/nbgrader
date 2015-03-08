from datetime import datetime
from nbgrader import api
from nbgrader.api import InvalidEntry, MissingEntry
from nose.tools import assert_equal, assert_not_equal, assert_raises

class TestGradebook(object):

    def setup(self):
        self.gb = api.Gradebook("sqlite:///:memory:")

    def teardown(self):
        self.gb.db.close()

    def test_init(self):
        assert_equal(self.gb.students, [], "students is not empty")
        assert_equal(self.gb.assignments, [], "assignments is not empty")

    #### Test students

    def test_add_student(self):
        s = self.gb.add_student('12345')
        assert_equal(s.id, '12345', "incorrect id")
        assert_equal(self.gb.students, [s], "student not in students")

        # try adding a duplicate student
        assert_raises(InvalidEntry, self.gb.add_student, '12345')

        # try adding a student with arguments
        s = self.gb.add_student('6789', last_name="Bar", first_name="Foo", email="foo@bar.com")
        assert_equal(s.id, '6789', "incorrect id")
        assert_equal(s.last_name, "Bar", "incorrect last name")
        assert_equal(s.first_name, "Foo", "incorrect first name")
        assert_equal(s.email, "foo@bar.com", "incorrect email")

    def test_add_duplicate_student(self):
        # we also need this test because this will cause an IntegrityError
        # under the hood rather than a FlushError
        self.gb.add_student('12345')
        assert_raises(InvalidEntry, self.gb.add_student, '12345')

    def test_find_student(self):
        s1 = self.gb.add_student('12345')
        assert_equal(self.gb.find_student('12345'), s1, "student 1 not found")

        s2 = self.gb.add_student('abcd')
        assert_equal(self.gb.find_student('12345'), s1, "student 1 not found after adding student 2")
        assert_equal(self.gb.find_student('abcd'), s2, "student 2 not found")

    def test_find_nonexistant_student(self):
        assert_raises(MissingEntry, self.gb.find_student, '12345')

    #### Test assignments

    def test_add_assignment(self):
        a = self.gb.add_assignment('foo')
        assert_equal(a.name, 'foo', "incorrect name")
        assert_equal(self.gb.assignments, [a], "assignment not in assignments")

        # try adding a duplicate assignment
        assert_raises(InvalidEntry, self.gb.add_assignment, 'foo')

        # try adding an assignment with arguments
        now = datetime.now()
        a = self.gb.add_assignment('bar', duedate=now)
        assert_equal(a.name, 'bar', "incorrect name")
        assert_equal(a.duedate, now, "incorrect duedate")

    def test_add_duplicate_assignment(self):
        self.gb.add_assignment('foo')
        assert_raises(InvalidEntry, self.gb.add_assignment, 'foo')

    def test_find_assignment(self):
        a1 = self.gb.add_assignment('foo')
        assert_equal(self.gb.find_assignment('foo'), a1, "assignment 1 not found")

        a2 = self.gb.add_assignment('bar')
        assert_equal(self.gb.find_assignment('foo'), a1, "assignment 1 not found after adding assignment 2")
        assert_equal(self.gb.find_assignment('bar'), a2, "assignment 2 not found")

    def test_find_nonexistant_assignment(self):
        assert_raises(MissingEntry, self.gb.find_assignment, 'foo')

    #### Test notebooks

    def test_add_notebook(self):
        a = self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        assert_equal(n.name, 'p1', "incorrect name")
        assert_equal(n.assignment, a, "assignment set incorrectly")
        assert_equal(a.notebooks, [n], "notebook set incorrectly")

        # try adding a duplicate assignment
        assert_raises(InvalidEntry, self.gb.add_notebook, 'p1', 'foo')

    def test_add_duplicate_notebook(self):
        # it should be ok to add a notebook with the same name, as long as
        # it's for different assignments
        self.gb.add_assignment('foo')
        self.gb.add_assignment('bar')
        n1 = self.gb.add_notebook('p1', 'foo')
        n2 = self.gb.add_notebook('p1', 'bar')
        assert_not_equal(n1.id, n2.id, "notebooks have the same id")

        # but not ok to add a notebook with the same name for the same assignment
        assert_raises(InvalidEntry, self.gb.add_notebook, 'p1', 'foo')

    def test_find_notebook(self):
        self.gb.add_assignment('foo')
        n1 = self.gb.add_notebook('p1', 'foo')
        assert_equal(self.gb.find_notebook('p1', 'foo'), n1, "notebook 1 not found")

        n2 = self.gb.add_notebook('p2', 'foo')
        assert_equal(self.gb.find_notebook('p1', 'foo'), n1, "notebook 1 not found after adding notebook 2")
        assert_equal(self.gb.find_notebook('p2', 'foo'), n2, "notebook 2 not found")

    def test_find_nonexistant_notebook(self):
        # check that it doesn't find it when there is nothing in the db
        assert_raises(MissingEntry, self.gb.find_notebook, 'p1', 'foo')

        # check that it doesn't find it even if the assignment exists
        self.gb.add_assignment('foo')
        assert_raises(MissingEntry, self.gb.find_notebook, 'p1', 'foo')

    def test_update_or_create_notebook(self):
        # first test creating it
        self.gb.add_assignment('foo')
        n1 = self.gb.update_or_create_notebook('p1', 'foo')
        assert_equal(self.gb.find_notebook('p1', 'foo'), n1, "notebook not created")

        # now test finding/updating it
        n2 = self.gb.update_or_create_notebook('p1', 'foo')
        assert_equal(n1, n2, "notebooks are not the same")

    #### Test grade cells

    def test_add_grade_cell(self):
        self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        gc = self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
        assert_equal(gc.name, 'test1', "incorrect name")
        assert_equal(gc.max_score, 2, "incorrect max score")
        assert_equal(gc.cell_type, 'markdown', "incorrect cell type")
        assert_equal(n.grade_cells, [gc], "grade cells set incorrectly")
        assert_equal(gc.notebook, n, "notebook set incorrectly")

    def test_add_grade_cell_with_args(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc = self.gb.add_grade_cell(
            'test1', 'p1', 'foo', 
            max_score=3, source="blah blah blah",
            cell_type="code", checksum="abcde")
        assert_equal(gc.name, 'test1', "incorrect name")
        assert_equal(gc.max_score, 3, "incorrect max score")
        assert_equal(gc.source, "blah blah blah", "incorrect source")
        assert_equal(gc.cell_type, "code", "incorrect cell type")
        assert_equal(gc.checksum, "abcde", "incorrect checksum")

    def test_create_invalid_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        assert_raises(
            InvalidEntry, self.gb.add_grade_cell,
            'test1', 'p1', 'foo', 
            max_score=3, source="blah blah blah",
            cell_type="something", checksum="abcde")

    def test_add_duplicate_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
        assert_raises(InvalidEntry, self.gb.add_grade_cell, 'test1', 'p1', 'foo', max_score=2, cell_type='markdown')

    def test_find_grade_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc1 = self.gb.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
        assert_equal(self.gb.find_grade_cell('test1', 'p1', 'foo'), gc1, "grade cell 1 not found")

        gc2 = self.gb.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='code')
        assert_equal(self.gb.find_grade_cell('test1', 'p1', 'foo'), gc1, "grade cell 1 not found after adding grade cell 2")
        assert_equal(self.gb.find_grade_cell('test2', 'p1', 'foo'), gc2, "grade cell 2 not found")

    def test_find_nonexistant_grade_cell(self):
        assert_raises(MissingEntry, self.gb.find_grade_cell, 'test1', 'p1', 'foo')

        self.gb.add_assignment('foo')
        assert_raises(MissingEntry, self.gb.find_grade_cell, 'test1', 'p1', 'foo')

        self.gb.add_notebook('p1', 'foo')
        assert_raises(MissingEntry, self.gb.find_grade_cell, 'test1', 'p1', 'foo')

    def test_update_or_create_grade_cell(self):
        # first test creating it
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        gc1 = self.gb.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='code')
        assert_equal(gc1.max_score, 2, "max score is incorrect")
        assert_equal(gc1.cell_type, 'code', "cell type is incorrect")
        assert_equal(self.gb.find_grade_cell('test1', 'p1', 'foo'), gc1, "grade cell not created")

        # now test finding/updating it
        assert_equal(gc1.checksum, None, "checksum is not empty")
        gc2 = self.gb.update_or_create_grade_cell('test1', 'p1', 'foo', checksum="123456")
        assert_equal(gc1, gc2, "grade cells are not the same")
        assert_equal(gc1.max_score, 2, "max score is incorrect")
        assert_equal(gc1.cell_type, 'code', "cell type is incorrect")
        assert_equal(gc1.checksum, "123456", "checksum was not updated")

    #### Test solution cells

    def test_add_solution_cell(self):
        self.gb.add_assignment('foo')
        n = self.gb.add_notebook('p1', 'foo')
        sc = self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        assert_equal(sc.name, 'test1', "incorrect name")
        assert_equal(sc.cell_type, 'code', "incorrect cell type")
        assert_equal(n.solution_cells, [sc], "solution cells set incorrectly")
        assert_equal(sc.notebook, n, "notebook set incorrectly")

    def test_add_solution_cell_with_args(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc = self.gb.add_solution_cell(
            'test1', 'p1', 'foo', 
            source="blah blah blah",
            cell_type="code", checksum="abcde")
        assert_equal(sc.name, 'test1', "incorrect name")
        assert_equal(sc.source, "blah blah blah", "incorrect source")
        assert_equal(sc.cell_type, "code", "incorrect cell type")
        assert_equal(sc.checksum, "abcde", "incorrect checksum")

    def test_create_invalid_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        assert_raises(
            InvalidEntry, self.gb.add_solution_cell,
            'test1', 'p1', 'foo', 
            source="blah blah blah",
            cell_type="something", checksum="abcde")

    def test_add_duplicate_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        assert_raises(InvalidEntry, self.gb.add_solution_cell, 'test1', 'p1', 'foo', cell_type="code")

    def test_find_solution_cell(self):
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc1 = self.gb.add_solution_cell('test1', 'p1', 'foo', cell_type="code")
        assert_equal(self.gb.find_solution_cell('test1', 'p1', 'foo'), sc1, "solution cell 1 not found")

        sc2 = self.gb.add_solution_cell('test2', 'p1', 'foo', cell_type="code")
        assert_equal(self.gb.find_solution_cell('test1', 'p1', 'foo'), sc1, "solution cell 1 not found after adding solution cell 2")
        assert_equal(self.gb.find_solution_cell('test2', 'p1', 'foo'), sc2, "solution cell 2 not found")

    def test_find_nonexistant_solution_cell(self):
        assert_raises(MissingEntry, self.gb.find_solution_cell, 'test1', 'p1', 'foo')

        self.gb.add_assignment('foo')
        assert_raises(MissingEntry, self.gb.find_solution_cell, 'test1', 'p1', 'foo')

        self.gb.add_notebook('p1', 'foo')
        assert_raises(MissingEntry, self.gb.find_solution_cell, 'test1', 'p1', 'foo')

    def test_update_or_create_solution_cell(self):
        # first test creating it
        self.gb.add_assignment('foo')
        self.gb.add_notebook('p1', 'foo')
        sc1 = self.gb.update_or_create_solution_cell('test1', 'p1', 'foo', cell_type='code')
        assert_equal(sc1.cell_type, 'code', "cell type is incorrect")
        assert_equal(self.gb.find_solution_cell('test1', 'p1', 'foo'), sc1, "solution cell not created")

        # now test finding/updating it
        assert_equal(sc1.checksum, None, "checksum is not empty")
        sc2 = self.gb.update_or_create_solution_cell('test1', 'p1', 'foo', checksum="123456")
        assert_equal(sc1, sc2, "solution cells are not the same")
        assert_equal(sc1.cell_type, 'code', "cell type is incorrect")
        assert_equal(sc1.checksum, "123456", "checksum was not updated")

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

        assert_equal(self.gb.assignment_submissions('foo'), [s2, s1], "wrong list of submissions")
        assert_equal(self.gb.student_submissions('hacker123'), [s1], "wrong submissions for hacker123")
        assert_equal(self.gb.student_submissions('bitdiddle'), [s2], "wrong submissions for bitdiddle")
        assert_equal(self.gb.find_submission('foo', 'hacker123'), s1, "couldn't find submission for hacker123")
        assert_equal(self.gb.find_submission('foo', 'bitdiddle'), s2, "couldn't find submission for bitdiddle")

    def test_add_duplicate_submission(self):
        self._add_assignment()
        self.gb.add_student('hacker123')
        self.gb.add_submission('foo', 'hacker123')
        assert_raises(InvalidEntry, self.gb.add_submission, 'foo', 'hacker123')


