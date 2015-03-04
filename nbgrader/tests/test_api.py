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
        assert a.average_score == 0
        assert a.average_code_score == 0
        assert a.average_written_score == 0

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
        assert n.average_score == 0
        assert n.average_code_score == 0
        assert n.average_written_score == 0

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
        s = api.SolutionCell(name='foo', notebook=n)
        self.db.add(a)
        self.db.commit()

        assert s.id
        assert s.name == 'foo'
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

        assert sa.duedate is None
        assert sa.timestamp is None
        assert sa.extension is None
        assert sa.total_seconds_late == 0

        d = sa.to_dict()
        assert d['id'] == sa.id
        assert d['name'] == 'foo'
        assert d['student'] == '12345'
        assert d['duedate'] is None
        assert d['timestamp'] is None
        assert d['extension'] is None
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
        assert sa.extension is None
        assert sa.total_seconds_late == 0

        d = sa.to_dict()
        assert d['duedate'] == duedate.isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] is None
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
        assert sa.extension is None
        assert sa.total_seconds_late == 172800

        d = sa.to_dict()
        assert d['duedate'] == duedate.isoformat()
        assert d['timestamp'] == timestamp.isoformat()
        assert d['extension'] is None
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
        assert g.manual_score is None
        assert g.assignment == sa
        assert g.student == s
        assert g.max_score == 10

        assert g.score == 5
        assert not g.needs_manual_grade
        assert sn.score == 5
        assert sn.code_score == 5
        assert sn.written_score == 0
        assert not sn.needs_manual_grade
        assert sa.score == 5
        assert sa.code_score == 5
        assert sa.written_score == 0
        assert not sa.needs_manual_grade
        assert n.average_score == 5
        assert n.average_code_score == 5
        assert n.average_written_score == 0
        assert a.average_score == 5
        assert a.average_code_score == 5
        assert a.average_written_score == 0
        assert s.score == 5

        g.manual_score = 7.5
        self.db.commit()

        assert g.score == 7.5
        assert not g.needs_manual_grade
        assert sn.score == 7.5
        assert sn.code_score == 7.5
        assert sn.written_score == 0
        assert not sn.needs_manual_grade
        assert sa.score == 7.5
        assert sa.code_score == 7.5
        assert sa.written_score == 0
        assert not sa.needs_manual_grade
        assert n.average_score == 7.5
        assert n.average_code_score == 7.5
        assert n.average_written_score == 0
        assert a.average_score == 7.5
        assert a.average_code_score == 7.5
        assert a.average_written_score == 0
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
        assert g.auto_score is None
        assert g.manual_score is None
        assert g.assignment == sa
        assert g.student == s
        assert g.max_score == 10

        assert g.score == 0
        assert g.needs_manual_grade
        assert sn.score == 0
        assert sn.code_score == 0
        assert sn.written_score == 0
        assert sn.needs_manual_grade
        assert sa.score == 0
        assert sa.code_score == 0
        assert sa.written_score == 0
        assert sa.needs_manual_grade
        assert n.average_score == 0
        assert n.average_code_score == 0
        assert n.average_written_score == 0
        assert a.average_score == 0
        assert a.average_code_score == 0
        assert a.average_written_score == 0
        assert s.score == 0

        g.manual_score = 7.5
        self.db.commit()

        assert g.score == 7.5
        assert not g.needs_manual_grade
        assert sn.score == 7.5
        assert sn.code_score == 0
        assert sn.written_score == 7.5
        assert not sn.needs_manual_grade
        assert sa.score == 7.5
        assert sa.code_score == 0
        assert sa.written_score == 7.5
        assert not sa.needs_manual_grade
        assert n.average_score == 7.5
        assert n.average_code_score == 0
        assert n.average_written_score == 7.5
        assert a.average_score == 7.5
        assert a.average_code_score == 0
        assert a.average_written_score == 7.5
        assert s.score == 7.5

    def test_create_comment(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        sc = api.SolutionCell(name='foo', notebook=n)
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

