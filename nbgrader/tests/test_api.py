from nbgrader import api

class TestApi(object):

    def test_create_assignment(self):
        a = api.Assignment(assignment_id='foo', duedate='someday')
        assert a.assignment_id == 'foo'
        assert a.duedate == 'someday'
        assert a._id

    def test_create_student(self):
        s = api.Student(student_id=12345, first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        assert s.student_id == 12345
        assert s.first_name == 'Jane'
        assert s.last_name == 'Doe'
        assert s.email == 'janedoe@nowhere'
        assert s._id

    def test_create_notebook(self):
        a = api.Assignment(assignment_id='foo', duedate='someday')
        s = api.Student(student_id=12345, first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        n = api.Notebook(notebook_id='blah', assignment=a, student=s)
        assert n.notebook_id == 'blah'
        assert n.assignment == a
        assert n.student == s
        assert n._id
        assert n.to_dict()['assignment'] == a._id
        assert n.to_dict()['student'] == s._id

    def test_create_grade(self):
        a = api.Assignment(assignment_id='foo', duedate='someday')
        s = api.Student(student_id=12345, first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        n = api.Notebook(notebook_id='blah', assignment=a, student=s)
        g = api.Grade(grade_id='foo', max_score=10, autoscore=1, score=5, notebook=n)
        assert g.grade_id == 'foo'
        assert g.max_score == 10
        assert g.autoscore == 1
        assert g.score == 5
        assert g.notebook == n
        assert g._id
        assert g.to_dict()['notebook'] == n._id

    def test_create_comment(self):
        a = api.Assignment(assignment_id='foo', duedate='someday')
        s = api.Student(student_id=12345, first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        n = api.Notebook(notebook_id='blah', assignment=a, student=s)
        c = api.Comment(comment_id='foo', comment='lorem ipsum', notebook=n)
        assert c.comment_id == 'foo'
        assert c.comment == 'lorem ipsum'
        assert c.notebook == n
        assert c._id
        assert c.to_dict()['notebook'] == n._id
