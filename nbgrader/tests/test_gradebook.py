from nbgrader import api
from pymongo.errors import DuplicateKeyError
from nose.tools import assert_equal, assert_raises

class TestGradebook(object):

    def setup(self):
        self.gb = api.Gradebook("nbgrader_testing")

    def teardown(self):
        self.gb.client.drop_database("nbgrader_testing")

    def _add_assignment(self):
        a = api.Assignment(assignment_id='foo', duedate='someday')
        self.gb.add_assignment(a)
        return a

    def _add_student(self):
        s = api.Student(student_id=12345, first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        self.gb.add_student(s)
        return s

    def _add_notebook(self):
        a = self._add_assignment()
        s = self._add_student()
        n = api.Notebook(notebook_id='blah', assignment=a, student=s)
        self.gb.add_notebook(n)
        return n

    def test_init(self):
        assert self.gb.students == []
        assert self.gb.notebooks == []
        assert self.gb.assignments == []

    def test_add_assignment(self):
        a = self._add_assignment()

        # try inserting a duplicate assignment
        assert_raises(DuplicateKeyError, self.gb.add_assignment, a)

        # try inserting something with the wrong type
        assert_raises(ValueError, self.gb.add_assignment, a.to_dict())

        # check that the assignment was correctly added
        assert len(self.gb.assignments) == 1
        assert_equal(self.gb.assignments[0].to_dict(), a.to_dict())
        assert_equal(self.gb.find_assignment(_id=a._id).to_dict(), a.to_dict())

        # try looking up a nonexistant assignment
        assert_raises(ValueError, self.gb.find_assignment, kwargs={'assignment_id': "bar"})

    def test_add_student(self):
        s = self._add_student()

        # try inserting a duplicate student
        assert_raises(DuplicateKeyError, self.gb.add_student, s)

        # try inserting something with the wrong type
        assert_raises(ValueError, self.gb.add_student, s.to_dict())

        # check that the student was correctly added
        assert len(self.gb.students) == 1
        assert_equal(self.gb.students[0].to_dict(), s.to_dict())
        assert_equal(self.gb.find_student(_id=s._id).to_dict(), s.to_dict())

        # try looking up a nonexistent stuent
        assert_raises(ValueError, self.gb.find_student, kwargs={'student_id': "bar"})

    def test_add_notebook(self):
        n1 = self._add_notebook()

        # try inserting a duplicate notebook
        assert_raises(DuplicateKeyError, self.gb.add_notebook, n1)

        # try inserting something with the wrong type
        assert_raises(ValueError, self.gb.add_notebook, n1.to_dict())

        # check that the notebook was correctly added
        assert len(self.gb.notebooks) == 1
        assert_equal(self.gb.notebooks[0].to_dict(), n1.to_dict())
        assert_equal(self.gb.find_notebook(_id=n1._id).to_dict(), n1.to_dict())

        # add another notebook for the same student but with a
        # different assignment
        a = self._add_assignment()
        n2 = api.Notebook(notebook_id='blargh', assignment=a, student=n1.student)
        self.gb.add_notebook(n2)

        # check that it was added correctly
        assert len(self.gb.notebooks) == 2
        assert_equal(self.gb.find_notebook(_id=n2._id).to_dict(), n2.to_dict())

        # check that both notebooks are associated with the student
        assert len(self.gb.find_notebooks(student=n1.student)) == 2

        # check that the first notebook is associated with the correct
        # assignment
        nbs = self.gb.find_notebooks(assignment=n1.assignment)
        assert len(nbs) == 1
        assert nbs[0]._id == n1._id

        # check that the second notebook is associated with the
        # correct assignment
        nbs = self.gb.find_notebooks(assignment=n2.assignment)
        assert len(nbs) == 1
        assert nbs[0]._id == n2._id

    def test_find_or_create_notebook(self):
        a = self._add_assignment()
        s = self._add_student()
        n1 = api.Notebook(notebook_id='blah', assignment=a, student=s)
        n2 = self.gb.find_or_create_notebook(**n1.to_dict())
        assert_equal(n1.to_dict(), n2.to_dict())

    def test_add_grade(self):
        n = self._add_notebook()
        g1 = api.Grade(grade_id='grade1', notebook=n, max_score=2)
        g2 = self.gb.find_or_create_grade(**g1.to_dict())
        assert_equal(g1.to_dict(), g2.to_dict())
        assert_equal(self.gb.find_grade(grade_id='grade1').to_dict(), g1.to_dict())

        grades = self.gb.find_grades(notebook=n)
        assert len(grades) == 1

        self.gb.find_or_create_grade(grade_id='grade2', notebook=n, max_score=3)
        grades = self.gb.find_grades(notebook=n)
        assert len(grades) == 2

        g1.autoscore = 1
        g1.score = 2
        self.gb.update_grade(g1)

        g = self.gb.find_grade(_id=g1._id)
        assert g.autoscore == 1
        assert g.score == 2

    def test_add_comment(self):
        n = self._add_notebook()
        c1 = api.Comment(comment_id="comment1", notebook=n)
        c2 = self.gb.find_or_create_comment(**c1.to_dict())
        assert_equal(c1.to_dict(), c2.to_dict())
        assert_equal(self.gb.find_comment(comment_id='comment1').to_dict(), c1.to_dict())

        comments = self.gb.find_comments(notebook=n)
        assert len(comments) == 1

        self.gb.find_or_create_comment(comment_id='comment2', notebook=n)
        comments = self.gb.find_comments(notebook=n)
        assert len(comments) == 2

        c1.comment = 'lorem ipsum'
        self.gb.update_comment(c1)

        g = self.gb.find_comment(_id=c1._id)
        assert g.comment == 'lorem ipsum'
