import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from nbgrader import api


class TestApi(object):

    def setup(self):
        engine = create_engine("sqlite:///:memory:")
        self.db = scoped_session(sessionmaker(autoflush=True, bind=engine))
        api.Base.query = self.db.query_property()
        api.Base.metadata.create_all(bind=engine)

    def test_create_assignment(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        self.db.add(a)
        self.db.commit()

        assert a.id
        assert a.name == 'foo'
        assert a.duedate == now
        assert a.notebooks == []
        assert a.submissions == []

        assert a.max_score == 0
        assert a.max_code_score == 0
        assert a.max_written_score == 0
        assert a.num_submissions == 0

    def test_create_notebook(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        self.db.add(a)
        self.db.commit()

        assert n.id
        assert n.name == 'blah'
        assert n.assignment == a
        assert n.grade_cells == []
        assert n.solution_cells == []
        assert n.submissions == []
        assert a.notebooks == [n]

        assert n.max_score == 0
        assert n.max_code_score == 0
        assert n.max_written_score == 0

    def test_create_grade_cell(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        g = api.GradeCell(
            name='foo', max_score=10, notebook=n, source="print('hello')", 
            cell_type="code", checksum="12345")
        self.db.add(a)
        self.db.commit()

        assert g.id
        assert g.name == 'foo'
        assert g.max_score == 10
        assert g.source == "print('hello')"
        assert g.cell_type == "code"
        assert g.checksum == "12345"
        assert g.assignment == a
        assert g.notebook == n
        assert g.grades == []
        assert n.grade_cells == [g]

        assert n.max_score == 10
        assert n.max_code_score == 10
        assert n.max_written_score == 0

    def test_create_solution_cell(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        s = api.SolutionCell(name='foo', notebook=n, source="hello", 
            cell_type="code", checksum="12345")
        self.db.add(a)
        self.db.commit()

        assert s.id
        assert s.name == 'foo'
        assert s.cell_type == "code"
        assert s.source == "hello"
        assert s.checksum == "12345"
        assert s.assignment == a
        assert s.notebook == n
        assert s.comments == []
        assert n.solution_cells == [s]

    def test_create_student(self):
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        self.db.add(s)
        self.db.commit()

        assert s.id == "12345"
        assert s.first_name == 'Jane'
        assert s.last_name == 'Doe'
        assert s.email == 'janedoe@nowhere'
        assert s.submissions == []

        assert s.score == 0
        assert s.max_score == 0

    def test_create_submitted_assignment(self):
        a = api.Assignment(name='foo')
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        self.db.add(sa)
        self.db.commit()

        assert sa.id
        assert sa.assignment == a
        assert sa.student == s
        assert sa.notebooks == []
        assert s.submissions == [sa]
        assert a.submissions == [sa]

        assert sa.score == 0
        assert sa.max_score == 0
        assert sa.code_score == 0
        assert sa.max_code_score == 0
        assert sa.written_score == 0
        assert sa.max_written_score == 0
        assert not sa.needs_manual_grade

        assert sa.duedate == None
        assert sa.timestamp == None
        assert sa.extension == None
        assert sa.total_seconds_late == 0

        d = sa.to_dict()
        assert d['id'] == sa.id
        assert d['name'] == 'foo'
        assert d['student'] == '12345'
        assert d['duedate'] == None
        assert d['timestamp'] == None
        assert d['extension'] == None
        assert d['total_seconds_late'] == 0
        assert d['score'] == 0
        assert d['max_score'] == 0
        assert d['code_score'] == 0
        assert d['max_code_score'] == 0
        assert d['written_score'] == 0
        assert d['max_written_score'] == 0
        assert not d['needs_manual_grade']

    def test_submission_timestamp_ontime(self):
        duedate = datetime.datetime.now()
        timestamp = duedate - datetime.timedelta(days=2)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp)
        self.db.add(sa)
        self.db.commit()

        assert sa.duedate == duedate
        assert sa.timestamp == timestamp
        assert sa.extension == None
        assert sa.total_seconds_late == 0

        d = sa.to_dict()
        assert d['duedate'] == duedate.isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] == None
        assert d['total_seconds_late'] == 0

    def test_submission_timestamp_late(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=2)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp)
        self.db.add(sa)
        self.db.commit()

        assert sa.duedate == duedate
        assert sa.timestamp == timestamp
        assert sa.extension == None
        assert sa.total_seconds_late == 172800

        d = sa.to_dict()
        assert d['duedate'] == duedate.isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] == None
        assert d['total_seconds_late'] == 172800

    def test_submission_timestamp_with_extension(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=2)
        extension = datetime.timedelta(days=3)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp, extension=extension)
        self.db.add(sa)
        self.db.commit()

        assert sa.duedate == (duedate + extension)
        assert sa.timestamp == timestamp
        assert sa.extension == extension
        assert sa.total_seconds_late == 0

        d = sa.to_dict()
        assert d['duedate'] == (duedate + extension).isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] == extension.total_seconds()
        assert d['total_seconds_late'] == 0

    def test_submission_timestamp_late_with_extension(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=5)
        extension = datetime.timedelta(days=3)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp, extension=extension)
        self.db.add(sa)
        self.db.commit()

        assert sa.duedate == (duedate + extension)
        assert sa.timestamp == timestamp
        assert sa.extension == extension
        assert sa.total_seconds_late == 172800

        d = sa.to_dict()
        assert d['duedate'] == (duedate + extension).isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] == extension.total_seconds()
        assert d['total_seconds_late'] == 172800

    def test_create_submitted_notebook(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        self.db.add(sn)
        self.db.commit()

        assert sn.id
        assert sn.notebook == n
        assert sn.assignment == sa
        assert sn.grades == []
        assert sn.comments == []
        assert sn.student == s
        assert sa.notebooks == [sn]
        assert n.submissions == [sn]

        assert sn.score == 0
        assert sn.max_score == 0
        assert sn.code_score == 0
        assert sn.max_code_score == 0
        assert sn.written_score == 0
        assert sn.max_written_score == 0
        assert not sn.needs_manual_grade

    def test_create_code_grade(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        gc = api.GradeCell(
            name='foo', max_score=10, notebook=n, source="print('hello')", 
            cell_type="code", checksum="12345")
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        g = api.Grade(cell=gc, notebook=sn, auto_score=5)
        self.db.add(g)
        self.db.commit()

        assert g.id
        assert g.cell == gc
        assert g.notebook == sn
        assert g.auto_score == 5
        assert g.manual_score == None
        assert g.assignment == sa
        assert g.student == s
        assert g.max_score == 10

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert g.score == 5
        assert sn.score == 5
        assert sn.code_score == 5
        assert sn.written_score == 0
        assert sa.score == 5
        assert sa.code_score == 5
        assert sa.written_score == 0
        assert s.score == 5

        g.manual_score = 7.5
        self.db.commit()

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert g.score == 7.5
        assert sn.score == 7.5
        assert sn.code_score == 7.5
        assert sn.written_score == 0
        assert sa.score == 7.5
        assert sa.code_score == 7.5
        assert sa.written_score == 0
        assert s.score == 7.5

    def test_create_written_grade(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        gc = api.GradeCell(
            name='foo', max_score=10, notebook=n, cell_type="markdown")
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        g = api.Grade(cell=gc, notebook=sn)
        self.db.add(g)
        self.db.commit()

        assert g.id
        assert g.cell == gc
        assert g.notebook == sn
        assert g.auto_score == None
        assert g.manual_score == None
        assert g.assignment == sa
        assert g.student == s
        assert g.max_score == 10

        assert g.needs_manual_grade
        assert sn.needs_manual_grade
        assert sa.needs_manual_grade

        assert g.score == 0
        assert sn.score == 0
        assert sn.code_score == 0
        assert sn.written_score == 0
        assert sa.score == 0
        assert sa.code_score == 0
        assert sa.written_score == 0
        assert s.score == 0

        g.manual_score = 7.5
        self.db.commit()

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert g.score == 7.5
        assert sn.score == 7.5
        assert sn.code_score == 0
        assert sn.written_score == 7.5
        assert sa.score == 7.5
        assert sa.code_score == 0
        assert sa.written_score == 7.5
        assert s.score == 7.5

    def test_create_comment(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        sc = api.SolutionCell(name='foo', notebook=n, cell_type="code")
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        c = api.Comment(cell=sc, notebook=sn, comment="something")
        self.db.add(c)
        self.db.commit()

        assert c.id
        assert c.cell == sc
        assert c.notebook == sn
        assert c.comment == "something"
        assert c.assignment == sa
        assert c.student == s

    def _init_submissions(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        gc1 = api.GradeCell(
            name='foo', max_score=10, notebook=n, cell_type="markdown")
        gc2 = api.GradeCell(
            name='bar', max_score=5, notebook=n, cell_type="code")
        self.db.add(a)
        self.db.commit()

        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        g1a = api.Grade(cell=gc1, notebook=sn)
        g2a = api.Grade(cell=gc2, notebook=sn)

        self.db.add(s)
        self.db.commit()

        s = api.Student(id="6789", first_name='John', last_name='Doe', email='johndoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        sn = api.SubmittedNotebook(assignment=sa, notebook=n)
        g1b = api.Grade(cell=gc1, notebook=sn)
        g2b = api.Grade(cell=gc2, notebook=sn)

        self.db.add(s)
        self.db.commit()

        return (g1a, g2a, g1b, g2b)

    def test_query_needs_manual_grade_ungraded(self):
        self._init_submissions()

        # do all the cells need grading?
        a = self.db.query(api.Grade)\
            .filter(api.Grade.needs_manual_grade)\
            .order_by(api.Grade.id)\
            .all()
        b = self.db.query(api.Grade)\
            .order_by(api.Grade.id)\
            .all()
        assert a == b

        # do all the notebooks need grading?
        a = self.db.query(api.SubmittedNotebook)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .order_by(api.SubmittedNotebook.id)\
            .all()
        b = self.db.query(api.SubmittedNotebook)\
            .order_by(api.SubmittedNotebook.id)\
            .all()
        assert a == b

        # do all the assignments need grading?
        a = self.db.query(api.SubmittedAssignment)\
            .join(api.SubmittedNotebook, api.Grade)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .order_by(api.SubmittedAssignment.id)\
            .all()
        b = self.db.query(api.SubmittedAssignment)\
            .order_by(api.SubmittedAssignment.id)\
            .all()
        assert a == b

    def test_query_needs_manual_grade_autograded(self):
        grades = self._init_submissions()

        for grade in grades:
            grade.auto_score = grade.max_score
        self.db.commit()

        # do none of the cells need grading?
        assert [] == self.db.query(api.Grade)\
            .filter(api.Grade.needs_manual_grade)\
            .all()

        # do none of the notebooks need grading?
        assert [] == self.db.query(api.SubmittedNotebook)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .all()

        # do none of the assignments need grading?
        assert [] == self.db.query(api.SubmittedAssignment)\
            .join(api.SubmittedNotebook, api.Grade)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .all()

    def test_query_needs_manual_grade_manualgraded(self):
        grades = self._init_submissions()

        for grade in grades:
            grade.auto_score = None
            grade.manual_score = grade.max_score / 2.0
        self.db.commit()

        # do none of the cells need grading?
        assert [] == self.db.query(api.Grade)\
            .filter(api.Grade.needs_manual_grade)\
            .all()

        # do none of the notebooks need grading?
        assert [] == self.db.query(api.SubmittedNotebook)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .all()

        # do none of the assignments need grading?
        assert [] == self.db.query(api.SubmittedAssignment)\
            .join(api.SubmittedNotebook, api.Grade)\
            .filter(api.SubmittedNotebook.needs_manual_grade)\
            .all()

    def test_query_max_score(self):
        self._init_submissions()

        assert [5, 10] == sorted([x[0] for x in self.db.query(api.GradeCell.max_score).all()])
        assert [5, 5, 10, 10] == sorted([x[1] for x in self.db.query(api.Grade.id, api.Grade.max_score).all()])
        assert [15] == sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_score).all()])
        assert [15, 15] == sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_score).all()])
        assert [15] == sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_score).all()])
        assert [15, 15] == sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_score).all()])
        assert [15, 15] == sorted([x[1] for x in self.db.query(api.Student.id, api.Student.max_score).all()])

    def test_query_score_ungraded(self):
        self._init_submissions()

        assert [x[0] for x in self.db.query(api.Grade.score).all()] == [0.0, 0.0, 0.0, 0.0]
        assert [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()] == [0.0, 0.0]
        assert [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()] == [0.0, 0.0]
        assert [x[1] for x in self.db.query(api.Student.id, api.Student.score).all()] == [0.0, 0.0]

    def test_query_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert sorted(x[0] for x in self.db.query(api.Grade.score).all()) == [0, 2.5, 5, 10]
        assert sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()) == [7.5, 10]
        assert sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()) == [7.5, 10]
        assert sorted(x[1] for x in self.db.query(api.Student.id, api.Student.score).all()) == [7.5, 10]

    def test_query_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 3
        self.db.commit()

        assert sorted(x[0] for x in self.db.query(api.Grade.score).all()) == [1.5, 3, 4, 9]
        assert sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()) == [5.5, 12]
        assert sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()) == [5.5, 12]
        assert sorted(x[1] for x in self.db.query(api.Student.id, api.Student.score).all()) == [5.5, 12]

    def test_query_max_written_score(self):
        self._init_submissions()

        assert [10] == sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_written_score).all()])
        assert [10, 10] == sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_written_score).all()])
        assert [10] == sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_written_score).all()])
        assert [10, 10] == sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_written_score).all()])

    def test_query_written_score_ungraded(self):
        self._init_submissions()

        assert [0.0, 0.0] == [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all()]
        assert [0.0, 0.0] == [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all()]

    def test_query_written_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert [5, 10] == sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all())
        assert [5, 10] == sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all())

    def test_query_written_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 3
        self.db.commit()

        assert [4, 9] == sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all())
        assert [4, 9] == sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all())

    def test_query_max_code_score(self):
        self._init_submissions()

        assert [5] == sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_code_score).all()])
        assert [5, 5] == sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_code_score).all()])
        assert [5] == sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_code_score).all()])
        assert [5, 5] == sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_code_score).all()])

    def test_query_code_score_ungraded(self):
        self._init_submissions()

        assert [0.0, 0.0] == [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all()]
        assert [0.0, 0.0] == [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all()]

    def test_query_code_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert [0, 2.5] == sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all())
        assert [0, 2.5] == sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all())

    def test_query_code_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 3
        self.db.commit()

        assert [1.5, 3] == sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all())
        assert [1.5, 3] == sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all())

    def test_query_num_submissions(self):
        self._init_submissions()

        assert [2] == [x[0] for x in self.db.query(api.Assignment.num_submissions).all()]
        assert [2] == [x[0] for x in self.db.query(api.Notebook.num_submissions).all()]

    def test_student_max_score(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        gc1 = api.GradeCell(
            name='foo', max_score=10, notebook=n, cell_type="markdown")
        gc2 = api.GradeCell(
            name='bar', max_score=5, notebook=n, cell_type="code")
        self.db.add(a)
        self.db.commit()

        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        self.db.add(s)
        self.db.commit()

        assert s.max_score == 15

    def test_query_grade_cell_types(self):
        self._init_submissions()

        a = self.db.query(api.Grade)\
            .filter(api.Grade.cell_type == "code")\
            .order_by(api.Grade.id)\
            .all()
        b = self.db.query(api.Grade)\
            .join(api.GradeCell)\
            .filter(api.GradeCell.cell_type == "code")\
            .order_by(api.Grade.id)\
            .all()
        assert a == b

        a = self.db.query(api.Grade)\
            .filter(api.Grade.cell_type == "markdown")\
            .order_by(api.Grade.id)\
            .all()
        b = self.db.query(api.Grade)\
            .join(api.GradeCell)\
            .filter(api.GradeCell.cell_type == "markdown")\
            .order_by(api.Grade.id)\
            .all()
        assert a == b

    def test_query_failed_tests_failed(self):
        grades = self._init_submissions()

        for grade in grades:
            if grade.cell.cell_type == "code":
                grade.auto_score = 0
        self.db.commit()

        # have all the cells failed?
        a = self.db.query(api.Grade)\
            .filter(api.Grade.failed_tests)\
            .order_by(api.Grade.id)\
            .all()
        b = self.db.query(api.Grade)\
            .filter(api.Grade.cell_type == "code")\
            .order_by(api.Grade.id)\
            .all()
        assert a == b

        # have all the notebooks failed?
        a = self.db.query(api.SubmittedNotebook)\
            .filter(api.SubmittedNotebook.failed_tests)\
            .order_by(api.SubmittedNotebook.id)\
            .all()
        b = self.db.query(api.SubmittedNotebook)\
            .order_by(api.SubmittedNotebook.id)\
            .all()

    def test_query_failed_tests_ok(self):
        all_grades = self._init_submissions()

        for grade in all_grades:
            if grade.cell.cell_type == "code":
                grade.auto_score = grade.max_score
        self.db.commit()

        # are all the grades ok?
        assert [] == self.db.query(api.Grade)\
            .filter(api.Grade.failed_tests)\
            .all()

        # are all the notebooks ok?
        assert [] == self.db.query(api.SubmittedNotebook)\
            .filter(api.SubmittedNotebook.failed_tests)\
            .all()
