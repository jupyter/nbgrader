import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from nose.tools import assert_equal as _assert_equal

from nbgrader import api

assert_equal = lambda x, y: _assert_equal(x, y)


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
        assert_equal(a.duedate, now)
        assert_equal(a.notebooks, [])
        assert_equal(a.submissions, [])

        assert_equal(a.max_score, 0)
        assert_equal(a.max_code_score, 0)
        assert_equal(a.max_written_score, 0)
        assert_equal(a.num_submissions, 0)
        assert_equal(a.average_score, 0)
        assert_equal(a.average_code_score, 0)
        assert_equal(a.average_written_score, 0)

    def test_create_notebook(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        self.db.add(a)
        self.db.commit()

        assert n.id
        assert_equal(n.name, 'blah')
        assert_equal(n.assignment, a)
        assert_equal(n.grade_cells, [])
        assert_equal(n.solution_cells, [])
        assert_equal(n.submissions, [])
        assert_equal(a.notebooks, [n])

        assert_equal(n.max_score, 0)
        assert_equal(n.max_code_score, 0)
        assert_equal(n.max_written_score, 0)
        assert_equal(n.average_score, 0)
        assert_equal(n.average_code_score, 0)
        assert_equal(n.average_written_score, 0)

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
        assert_equal(g.name, 'foo')
        assert_equal(g.max_score, 10)
        assert_equal(g.source, "print('hello')")
        assert_equal(g.cell_type, "code")
        assert_equal(g.checksum, "12345")
        assert_equal(g.assignment, a)
        assert_equal(g.notebook, n)
        assert_equal(g.grades, [])
        assert_equal(n.grade_cells, [g])

        assert_equal(n.max_score, 10)
        assert_equal(n.max_code_score, 10)
        assert_equal(n.max_written_score, 0)

    def test_create_solution_cell(self):
        now = datetime.datetime.now()
        a = api.Assignment(name='foo', duedate=now)
        n = api.Notebook(name='blah', assignment=a)
        s = api.SolutionCell(name='foo', notebook=n, source="hello", 
            cell_type="code", checksum="12345")
        self.db.add(a)
        self.db.commit()

        assert s.id
        assert_equal(s.name, 'foo')
        assert_equal(s.cell_type, "code")
        assert_equal(s.source, "hello")
        assert_equal(s.checksum, "12345")
        assert_equal(s.assignment, a)
        assert_equal(s.notebook, n)
        assert_equal(s.comments, [])
        assert_equal(n.solution_cells, [s])

    def test_create_student(self):
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        self.db.add(s)
        self.db.commit()

        assert_equal(s.id, "12345")
        assert_equal(s.first_name, 'Jane')
        assert_equal(s.last_name, 'Doe')
        assert_equal(s.email, 'janedoe@nowhere')
        assert_equal(s.submissions, [])

        assert_equal(s.score, 0)
        assert_equal(s.max_score, 0)

    def test_create_submitted_assignment(self):
        a = api.Assignment(name='foo')
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s)
        self.db.add(sa)
        self.db.commit()

        assert sa.id
        assert_equal(sa.assignment, a)
        assert_equal(sa.student, s)
        assert_equal(sa.notebooks, [])
        assert_equal(s.submissions, [sa])
        assert_equal(a.submissions, [sa])

        assert_equal(sa.score, 0)
        assert_equal(sa.max_score, 0)
        assert_equal(sa.code_score, 0)
        assert_equal(sa.max_code_score, 0)
        assert_equal(sa.written_score, 0)
        assert_equal(sa.max_written_score, 0)
        assert not sa.needs_manual_grade

        assert_equal(sa.duedate, None)
        assert_equal(sa.timestamp, None)
        assert_equal(sa.extension, None)
        assert_equal(sa.total_seconds_late, 0)

        d = sa.to_dict()
        assert_equal(d['id'], sa.id)
        assert_equal(d['name'], 'foo')
        assert_equal(d['student'], '12345')
        assert_equal(d['duedate'], None)
        assert_equal(d['timestamp'], None)
        assert_equal(d['extension'], None)
        assert_equal(d['total_seconds_late'], 0)
        assert_equal(d['score'], 0)
        assert_equal(d['max_score'], 0)
        assert_equal(d['code_score'], 0)
        assert_equal(d['max_code_score'], 0)
        assert_equal(d['written_score'], 0)
        assert_equal(d['max_written_score'], 0)
        assert not d['needs_manual_grade']

    def test_submission_timestamp_ontime(self):
        duedate = datetime.datetime.now()
        timestamp = duedate - datetime.timedelta(days=2)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp)
        self.db.add(sa)
        self.db.commit()

        assert_equal(sa.duedate, duedate)
        assert_equal(sa.timestamp, timestamp)
        assert_equal(sa.extension, None)
        assert_equal(sa.total_seconds_late, 0)

        d = sa.to_dict()
        assert_equal(d['duedate'], duedate.isoformat())
        assert_equal(d['timestamp'], timestamp.isoformat())
        assert_equal(d['extension'], None)
        assert_equal(d['total_seconds_late'], 0)

    def test_submission_timestamp_late(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=2)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp)
        self.db.add(sa)
        self.db.commit()

        assert_equal(sa.duedate, duedate)
        assert_equal(sa.timestamp, timestamp)
        assert_equal(sa.extension, None)
        assert_equal(sa.total_seconds_late, 172800)

        d = sa.to_dict()
        assert_equal(d['duedate'], duedate.isoformat())
        assert_equal(d['timestamp'], timestamp.isoformat())
        assert_equal(d['extension'], None)
        assert_equal(d['total_seconds_late'], 172800)

    def test_submission_timestamp_with_extension(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=2)
        extension = datetime.timedelta(days=3)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp, extension=extension)
        self.db.add(sa)
        self.db.commit()

        assert_equal(sa.duedate, (duedate + extension))
        assert_equal(sa.timestamp, timestamp)
        assert_equal(sa.extension, extension)
        assert_equal(sa.total_seconds_late, 0)

        d = sa.to_dict()
        assert_equal(d['duedate'], (duedate + extension).isoformat())
        assert_equal(d['timestamp'], timestamp.isoformat())
        assert_equal(d['extension'], extension.total_seconds())
        assert_equal(d['total_seconds_late'], 0)

    def test_submission_timestamp_late_with_extension(self):
        duedate = datetime.datetime.now()
        timestamp = duedate + datetime.timedelta(days=5)
        extension = datetime.timedelta(days=3)

        a = api.Assignment(name='foo', duedate=duedate)
        s = api.Student(id="12345", first_name='Jane', last_name='Doe', email='janedoe@nowhere')
        sa = api.SubmittedAssignment(assignment=a, student=s, timestamp=timestamp, extension=extension)
        self.db.add(sa)
        self.db.commit()

        assert_equal(sa.duedate, (duedate + extension))
        assert_equal(sa.timestamp, timestamp)
        assert_equal(sa.extension, extension)
        assert_equal(sa.total_seconds_late, 172800)

        d = sa.to_dict()
        assert_equal(d['duedate'], (duedate + extension).isoformat())
        assert_equal(d['timestamp'], timestamp.isoformat())
        assert_equal(d['extension'], extension.total_seconds())
        assert_equal(d['total_seconds_late'], 172800)

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
        assert_equal(sn.notebook, n)
        assert_equal(sn.assignment, sa)
        assert_equal(sn.grades, [])
        assert_equal(sn.comments, [])
        assert_equal(sn.student, s)
        assert_equal(sa.notebooks, [sn])
        assert_equal(n.submissions, [sn])

        assert_equal(sn.score, 0)
        assert_equal(sn.max_score, 0)
        assert_equal(sn.code_score, 0)
        assert_equal(sn.max_code_score, 0)
        assert_equal(sn.written_score, 0)
        assert_equal(sn.max_written_score, 0)
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
        assert_equal(g.cell, gc)
        assert_equal(g.notebook, sn)
        assert_equal(g.auto_score, 5)
        assert_equal(g.manual_score, None)
        assert_equal(g.assignment, sa)
        assert_equal(g.student, s)
        assert_equal(g.max_score, 10)

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert_equal(g.score, 5)
        assert_equal(sn.score, 5)
        assert_equal(sn.code_score, 5)
        assert_equal(sn.written_score, 0)
        assert_equal(sa.score, 5)
        assert_equal(sa.code_score, 5)
        assert_equal(sa.written_score, 0)
        assert_equal(n.average_score, 5)
        assert_equal(n.average_code_score, 5)
        assert_equal(n.average_written_score, 0)
        assert_equal(a.average_score, 5)
        assert_equal(a.average_code_score, 5)
        assert_equal(a.average_written_score, 0)
        assert_equal(s.score, 5)

        g.manual_score = 7.5
        self.db.commit()

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert_equal(g.score, 7.5)
        assert_equal(sn.score, 7.5)
        assert_equal(sn.code_score, 7.5)
        assert_equal(sn.written_score, 0)
        assert_equal(sa.score, 7.5)
        assert_equal(sa.code_score, 7.5)
        assert_equal(sa.written_score, 0)
        assert_equal(n.average_score, 7.5)
        assert_equal(n.average_code_score, 7.5)
        assert_equal(n.average_written_score, 0)
        assert_equal(a.average_score, 7.5)
        assert_equal(a.average_code_score, 7.5)
        assert_equal(a.average_written_score, 0)
        assert_equal(s.score, 7.5)

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
        assert_equal(g.cell, gc)
        assert_equal(g.notebook, sn)
        assert_equal(g.auto_score, None)
        assert_equal(g.manual_score, None)
        assert_equal(g.assignment, sa)
        assert_equal(g.student, s)
        assert_equal(g.max_score, 10)

        assert g.needs_manual_grade
        assert sn.needs_manual_grade
        assert sa.needs_manual_grade

        assert_equal(g.score, 0)
        assert_equal(sn.score, 0)
        assert_equal(sn.code_score, 0)
        assert_equal(sn.written_score, 0)
        assert_equal(sa.score, 0)
        assert_equal(sa.code_score, 0)
        assert_equal(sa.written_score, 0)
        assert_equal(n.average_score, 0)
        assert_equal(n.average_code_score, 0)
        assert_equal(n.average_written_score, 0)
        assert_equal(a.average_score, 0)
        assert_equal(a.average_code_score, 0)
        assert_equal(a.average_written_score, 0)
        assert_equal(s.score, 0)

        g.manual_score = 7.5
        self.db.commit()

        assert not g.needs_manual_grade
        assert not sn.needs_manual_grade
        assert not sa.needs_manual_grade

        assert_equal(g.score, 7.5)
        assert_equal(sn.score, 7.5)
        assert_equal(sn.code_score, 0)
        assert_equal(sn.written_score, 7.5)
        assert_equal(sa.score, 7.5)
        assert_equal(sa.code_score, 0)
        assert_equal(sa.written_score, 7.5)
        assert_equal(n.average_score, 7.5)
        assert_equal(n.average_code_score, 0)
        assert_equal(n.average_written_score, 7.5)
        assert_equal(a.average_score, 7.5)
        assert_equal(a.average_code_score, 0)
        assert_equal(a.average_written_score, 7.5)
        assert_equal(s.score, 7.5)

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
        assert_equal(c.cell, sc)
        assert_equal(c.notebook, sn)
        assert_equal(c.comment, "something")
        assert_equal(c.assignment, sa)
        assert_equal(c.student, s)

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
        assert_equal(
            self.db.query(api.Grade)\
                .filter(api.Grade.needs_manual_grade)\
                .order_by(api.Grade.id)\
                .all(),
            self.db.query(api.Grade)\
                .order_by(api.Grade.id)\
                .all()
        )

        # do all the notebooks need grading?
        assert_equal(
            self.db.query(api.SubmittedNotebook)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .order_by(api.SubmittedNotebook.id)\
                .all(),
            self.db.query(api.SubmittedNotebook)\
                .order_by(api.SubmittedNotebook.id)\
                .all()
        )

        # do all the assignments need grading?
        assert_equal(
            self.db.query(api.SubmittedAssignment)\
                .join(api.SubmittedNotebook, api.Grade)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .order_by(api.SubmittedAssignment.id)\
                .all(),
            self.db.query(api.SubmittedAssignment)\
                .order_by(api.SubmittedAssignment.id)\
                .all()
        )

    def test_query_needs_manual_grade_autograded(self):
        grades = self._init_submissions()

        for grade in grades:
            grade.auto_score = grade.max_score
        self.db.commit()

        # do none of the cells need grading?
        assert_equal(
            self.db.query(api.Grade)\
                .filter(api.Grade.needs_manual_grade)\
                .all(),
            [])

        # do none of the notebooks need grading?
        assert_equal(
            self.db.query(api.SubmittedNotebook)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .all(),
            [])

        # do none of the assignments need grading?
        assert_equal(
            self.db.query(api.SubmittedAssignment)\
                .join(api.SubmittedNotebook, api.Grade)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .all(),
            [])

    def test_query_needs_manual_grade_manualgraded(self):
        grades = self._init_submissions()

        for grade in grades:
            grade.auto_score = None
            grade.manual_score = grade.max_score / 2.0
        self.db.commit()

        # do none of the cells need grading?
        assert_equal(
            self.db.query(api.Grade)\
                .filter(api.Grade.needs_manual_grade)\
                .all(),
            [])

        # do none of the notebooks need grading?
        assert_equal(
            self.db.query(api.SubmittedNotebook)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .all(),
            [])

        # do none of the assignments need grading?
        assert_equal(
            self.db.query(api.SubmittedAssignment)\
                .join(api.SubmittedNotebook, api.Grade)\
                .filter(api.SubmittedNotebook.needs_manual_grade)\
                .all(),
            [])

    def test_query_max_score(self):
        self._init_submissions()

        assert_equal(
            sorted([x[0] for x in self.db.query(api.GradeCell.max_score).all()]),
            [5, 10])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Grade.id, api.Grade.max_score).all()]),
            [5, 5, 10, 10])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_score).all()]),
            [15])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_score).all()]),
            [15, 15])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_score).all()]),
            [15])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_score).all()]),
            [15, 15])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Student.id, api.Student.max_score).all()]),
            [15, 15])

    def test_query_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[0] for x in self.db.query(api.Grade.score).all()], 
            [0.0, 0.0, 0.0, 0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()],
            [0.0, 0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()], 
            [0.0, 0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.Student.id, api.Student.score).all()], 
            [0.0, 0.0])

    def test_query_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            sorted(x[0] for x in self.db.query(api.Grade.score).all()),
            [0, 2.5, 5, 10])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()),
            [7.5, 10])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()),
            [7.5, 10])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.Student.id, api.Student.score).all()),
            [7.5, 10])

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

        assert_equal(
            sorted(x[0] for x in self.db.query(api.Grade.score).all()),
            [1.5, 3, 4, 9])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.score).all()),
            [5.5, 12])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.score).all()),
            [5.5, 12])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.Student.id, api.Student.score).all()),
            [5.5, 12])

    def test_query_max_written_score(self):
        self._init_submissions()

        assert_equal(
            sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_written_score).all()]),
            [10])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_written_score).all()]),
            [10, 10])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_written_score).all()]),
            [10])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_written_score).all()]),
            [10, 10])

    def test_query_written_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all()],
            [0.0, 0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all()], 
            [0.0, 0.0])

    def test_query_written_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all()),
            [5, 10])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all()),
            [5, 10])

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

        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.written_score).all()),
            [4, 9])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.written_score).all()),
            [4, 9])

    def test_query_max_code_score(self):
        self._init_submissions()

        assert_equal(
            sorted([x[1] for x in self.db.query(api.Notebook.id, api.Notebook.max_code_score).all()]),
            [5])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.max_code_score).all()]),
            [5, 5])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.Assignment.id, api.Assignment.max_code_score).all()]),
            [5])
        assert_equal(
            sorted([x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.max_code_score).all()]),
            [5, 5])

    def test_query_code_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all()],
            [0.0, 0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all()], 
            [0.0, 0.0])

    def test_query_code_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all()),
            [0, 2.5])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all()),
            [0, 2.5])

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

        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedNotebook.id, api.SubmittedNotebook.code_score).all()),
            [1.5, 3])
        assert_equal(
            sorted(x[1] for x in self.db.query(api.SubmittedAssignment.id, api.SubmittedAssignment.code_score).all()),
            [1.5, 3])

    def test_query_average_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_score).all()],
            [0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_score).all()],
            [0.0])

    def test_query_average_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_score).all()],
            [8.75])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_score).all()],
            [8.75])

    def test_query_average_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 2
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_score).all()],
            [8.25])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_score).all()],
            [8.25])

    def test_query_average_code_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_code_score).all()],
            [0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_code_score).all()],
            [0.0])

    def test_query_average_code_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_code_score).all()],
            [1.25])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_code_score).all()],
            [1.25])

    def test_query_average_code_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 2
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_code_score).all()],
            [1.75])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_code_score).all()],
            [1.75])

    def test_query_average_written_score_ungraded(self):
        self._init_submissions()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_written_score).all()],
            [0.0])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_written_score).all()],
            [0.0])

    def test_query_average_written_score_autograded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_written_score).all()],
            [7.5])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_written_score).all()],
            [7.5])

    def test_query_average_written_score_manualgraded(self):
        grades = self._init_submissions()

        grades[0].auto_score = 10
        grades[1].auto_score = 0
        grades[2].auto_score = 5
        grades[3].auto_score = 2.5
        grades[0].manual_score = 4
        grades[1].manual_score = 1.5
        grades[2].manual_score = 9
        grades[3].manual_score = 2
        self.db.commit()

        assert_equal(
            [x[1] for x in self.db.query(api.Notebook.id, api.Notebook.average_written_score).all()],
            [6.5])
        assert_equal(
            [x[1] for x in self.db.query(api.Assignment.id, api.Assignment.average_written_score).all()],
            [6.5])

    def test_query_num_submissions(self):
        self._init_submissions()

        assert_equal(
            [x[0] for x in self.db.query(api.Assignment.num_submissions).all()],
            [2])



