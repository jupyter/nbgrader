from __future__ import division

from sqlalchemy import create_engine, ForeignKey, Column, String, Text, DateTime, Float, Enum, UniqueConstraint
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.exc import IntegrityError

from uuid import uuid4

Base = declarative_base()

class InvalidEntry(ValueError):
    pass


def new_uuid():
    return uuid4().hex


def mean(x):
    if len(x) == 0:
        return 0.0
    else:
        return sum(x) / len(x)


class Assignment(Base):
    __tablename__ = "assignment"

    id = Column(String(32), primary_key=True, default=new_uuid)
    name = Column(String(128), unique=True, nullable=False)
    duedate = Column(DateTime())

    notebooks = relationship("Notebook", backref="assignment", order_by="Notebook.name")
    submissions = relationship("SubmittedAssignment", backref="assignment")

    @property
    def max_score(self):
        return sum([n.max_score for n in self.notebooks])

    @property
    def max_code_score(self):
        return sum([n.max_code_score for n in self.notebooks])

    @property
    def max_written_score(self):
        return sum([n.max_written_score for n in self.notebooks])

    @property
    def num_submissions(self):
        return len(self.submissions)

    @property
    def average_score(self):
        return mean([n.score for n in self.submissions])

    @property
    def average_code_score(self):
        return mean([n.code_score for n in self.submissions])

    @property
    def average_written_score(self):
        return mean([n.written_score for n in self.submissions])

    def to_dict(self):
        return {
            "name": self.name,
            "duedate": self.duedate,
            "num_submissions": self.num_submissions,
            "average_score": self.average_score,
            "max_score": self.max_score,
            "average_code_score": self.average_code_score,
            "max_code_score": self.max_code_score,
            "average_written_score": self.average_written_score,
            "max_written_score": self.max_written_score,
        }

    def __repr__(self):
        return self.name

class Notebook(Base):
    __tablename__ = "notebook"
    __table_args__ = (UniqueConstraint('name', 'assignment_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    name = Column(String(128), nullable=False)

    assignment_id = Column(String(32), ForeignKey('assignment.id'))

    grade_cells = relationship("GradeCell", backref="notebook")
    solution_cells = relationship("SolutionCell", backref="notebook")

    submissions = relationship("SubmittedNotebook", backref="notebook")

    @property
    def max_score(self):
        return sum([g.max_score for g in self.grade_cells])

    @property
    def max_code_score(self):
        return sum([g.max_score for g in self.grade_cells if g.cell_type == "code"])

    @property
    def max_written_score(self):
        return sum([g.max_score for g in self.grade_cells if g.cell_type == "markdown"])

    @property
    def average_score(self):
        return mean([n.score for n in self.submissions])

    @property
    def average_code_score(self):
        return mean([n.code_score for n in self.submissions])

    @property
    def average_written_score(self):
        return mean([n.written_score for n in self.submissions])

    def to_dict(self):
        return {
            "name": self.name,
            "max_score": self.max_score,
            "max_code_score": self.max_code_score,
            "max_written_score": self.max_written_score,
            "average_score": self.average_score,
            "average_code_score": self.average_code_score,
            "average_written_score": self.average_written_score
        }        

    def __repr__(self):
        return "{}/{}".format(self.assignment, self.name)


class GradeCell(Base):
    __tablename__ = "grade_cell"
    __table_args__ = (UniqueConstraint('name', 'notebook_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    name = Column(String(128), nullable=False)
    max_score = Column(Float(), nullable=False)
    cell_type = Column(Enum("code", "markdown"), nullable=False)
    source = Column(Text())
    checksum = Column(String(128))

    notebook_id = Column(String(32), ForeignKey('notebook.id'))

    assignment = association_proxy("notebook", "assignment")

    grades = relationship("Grade", backref="cell")

    def __repr__(self):
        return "{}/{}".format(self.notebook, self.name)


class SolutionCell(Base):
    __tablename__ = "solution_cell"
    __table_args__ = (UniqueConstraint('name', 'notebook_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    name = Column(String(128), nullable=False)

    notebook_id = Column(String(32), ForeignKey('notebook.id'))

    assignment = association_proxy("notebook", "assignment")

    comments = relationship("Comment", backref="cell")

    def __repr__(self):
        return "{}/{}".format(self.notebook, self.name)


class Student(Base):
    __tablename__ = "student"

    id = Column(String(128), primary_key=True, nullable=False)
    first_name = Column(String(128))
    last_name = Column(String(128))
    email = Column(String(128))

    submissions = relationship("SubmittedAssignment", backref="student")

    @property
    def score(self):
        return sum([s.score for s in self.submissions])

    @property
    def max_score(self):
        return sum([s.max_score for s in self.submissions])

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "score": self.score,
            "max_score": self.max_score
        }

    def __repr__(self):
        return self.id


class SubmittedAssignment(Base):
    __tablename__ = "submitted_assignment"
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    assignment_id = Column(String(32), ForeignKey('assignment.id'))
    student_id = Column(String(128), ForeignKey('student.id'))

    notebooks = relationship("SubmittedNotebook", backref="assignment")

    @property
    def score(self):
        return sum([n.score for n in self.notebooks])

    @property
    def max_score(self):
        return self.assignment.max_score

    @property
    def code_score(self):
        return sum([n.code_score for n in self.notebooks])

    @property
    def max_code_score(self):
        return self.assignment.max_code_score

    @property
    def written_score(self):
        return sum([n.written_score for n in self.notebooks])

    @property
    def max_written_score(self):
        return self.assignment.max_written_score

    @property
    def needs_manual_grade(self):
        return any([n.needs_manual_grade for n in self.notebooks])

    def to_dict(self):
        return {
            "name": self.assignment.name,
            "student": self.student.id,
            "duedate": self.assignment.duedate,
            "score": self.score,
            "max_score": self.max_score,
            "code_score": self.code_score,
            "max_code_score": self.max_code_score,
            "written_score": self.written_score,
            "max_written_score": self.max_written_score,
            "needs_manual_grade": self.needs_manual_grade
        }

    def __repr__(self):
        return "{} for {}".format(self.assignment, self.student)


class SubmittedNotebook(Base):
    __tablename__ = "submitted_notebook"
    __table_args__ = (UniqueConstraint('notebook_id', 'assignment_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    notebook_id = Column(String(32), ForeignKey('notebook.id'))
    assignment_id = Column(String(32), ForeignKey('submitted_assignment.id'))

    grades = relationship("Grade", backref="notebook")
    comments = relationship("Comment", backref="notebook")

    student = association_proxy('assignment', 'student')

    @property
    def score(self):
        return sum([g.score for g in self.grades])

    @property
    def max_score(self):
        return self.notebook.max_score

    @property
    def code_score(self):
        return sum([g.score for g in self.grades if g.cell.cell_type == "code"])

    @property
    def max_code_score(self):
        return self.notebook.max_code_score

    @property
    def written_score(self):
        return sum([g.score for g in self.grades if g.cell.cell_type == "markdown"])

    @property
    def max_written_score(self):
        return self.notebook.max_written_score

    @property
    def needs_manual_grade(self):
        return any([g.needs_manual_grade for g in self.grades])

    def to_dict(self):
        return {
            "name": self.notebook.name,
            "student": self.student.to_dict(),
            "score": self.score,
            "max_score": self.max_score,
            "code_score": self.code_score,
            "max_code_score": self.max_code_score,
            "written_score": self.written_score,
            "max_written_score": self.max_written_score,
            "needs_manual_grade": self.needs_manual_grade
        }

    def __repr__(self):
        return "{} for {}".format(self.notebook, self.student)


class Grade(Base):
    __tablename__ = "grade"
    __table_args__ = (UniqueConstraint('cell_id', 'notebook_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    cell_id = Column(String(32), ForeignKey('grade_cell.id'))
    notebook_id = Column(String(32), ForeignKey('submitted_notebook.id'))

    auto_score = Column(Float())
    manual_score = Column(Float())

    assignment = association_proxy('notebook', 'assignment')
    student = association_proxy('notebook', 'student')
    max_score = association_proxy('cell', 'max_score')

    @property
    def score(self):
        if self.manual_score is not None:
            return self.manual_score
        elif self.auto_score is not None:
            return self.auto_score
        else:
            return 0.0

    @property
    def needs_manual_grade(self):
        return self.cell.cell_type == "markdown" and self.manual_score is None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.cell.name,
            "notebook": self.notebook.notebook.name,
            "assignment": self.assignment.assignment.name,
            "student": self.student.id,
            "auto_score": self.auto_score,
            "manual_score": self.manual_score,
            "max_score": self.max_score,
            "needs_manual_grade": self.needs_manual_grade
        }

    def __repr__(self):
        return "{} for {}".format(self.cell, self.student)


class Comment(Base):
    __tablename__ = "comment"
    __table_args__ = (UniqueConstraint('cell_id', 'notebook_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    cell_id = Column(String(32), ForeignKey('solution_cell.id'))
    notebook_id = Column(String(32), ForeignKey('submitted_notebook.id'))

    comment = Column(Text())

    assignment = association_proxy('notebook', 'assignment')
    student = association_proxy('notebook', 'student')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.cell.name,
            "notebook": self.notebook.notebook.name,
            "assignment": self.assignment.assignment.name,
            "student": self.student.id,
            "comment": self.comment,
        }

    def __repr__(self):
        return "{} for {}".format(self.cell, self.student)


class Gradebook(object):

    def __init__(self, db_url):
        # create the connection to the database
        engine = create_engine(db_url)
        self.db = scoped_session(sessionmaker(autoflush=True, bind=engine))
        Base.query = self.db.query_property()
        Base.metadata.create_all(bind=engine)

    #### Students

    @property
    def students(self):
        return self.db.query(Student)\
            .order_by(Student.last_name, Student.first_name)\
            .all()

    def add_student(self, student_id, **kwargs):
        student = Student(id=student_id, **kwargs)
        self.db.add(student)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)
        return student

    def find_student(self, student_id):
        return self.db.query(Student)\
            .filter(Student.id == student_id)\
            .one()

    #### Assignments

    @property
    def assignments(self):
        return self.db.query(Assignment)\
            .order_by(Assignment.duedate, Assignment.name)\
            .all()

    def add_assignment(self, name, **kwargs):
        assignment = Assignment(name=name, **kwargs)
        self.db.add(assignment)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)
        return assignment

    def find_assignment(self, name):
        return self.db.query(Assignment)\
            .filter(Assignment.name == name)\
            .one()

    #### Notebooks

    def add_notebook(self, name, assignment, **kwargs):
        notebook = Notebook(
            name=name, assignment=self.find_assignment(assignment), **kwargs)
        self.db.add(notebook)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)
        return notebook

    def find_notebook(self, name, assignment):
        return self.db.query(Notebook)\
            .join(Assignment, Assignment.id == Notebook.assignment_id)\
            .filter(Notebook.name == name, Assignment.name == assignment)\
            .one()

    def update_or_create_notebook(self, name, assignment, **kwargs):
        try:
            notebook = self.find_notebook(name, assignment)
        except NoResultFound:
            notebook = self.add_notebook(name, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(notebook, attr, kwargs[attr])
            self.db.commit()

        return notebook

    #### Grade cells

    def add_grade_cell(self, name, notebook, assignment, **kwargs):
        notebook = self.find_notebook(notebook, assignment)
        grade_cell = GradeCell(name=name, notebook=notebook, **kwargs)
        self.db.add(grade_cell)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)
        return grade_cell

    def find_grade_cell(self, name, notebook, assignment):
        return self.db.query(GradeCell)\
            .join(Notebook, Notebook.id == GradeCell.notebook_id)\
            .join(Assignment, Assignment.id == Notebook.assignment_id)\
            .filter(
                GradeCell.name == name,
                Notebook.name == notebook,
                Assignment.name == assignment)\
            .one()

    def update_or_create_grade_cell(self, name, notebook, assignment, **kwargs):
        try:
            grade_cell = self.find_grade_cell(name, notebook, assignment)
        except NoResultFound:
            grade_cell = self.add_grade_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(grade_cell, attr, kwargs[attr])
            self.db.commit()

        return grade_cell

    #### Solution cells

    def add_solution_cell(self, name, notebook, assignment, **kwargs):
        notebook = self.find_notebook(notebook, assignment)
        solution_cell = SolutionCell(name=name, notebook=notebook, **kwargs)
        self.db.add(solution_cell)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)
        return solution_cell

    def find_solution_cell(self, name, notebook, assignment):
        return self.db.query(SolutionCell)\
            .join(Notebook, Notebook.id == SolutionCell.notebook_id)\
            .join(Assignment, Assignment.id == Notebook.assignment_id)\
            .filter(SolutionCell.name == name, Notebook.name == notebook, Assignment.name == assignment)\
            .one()

    def update_or_create_solution_cell(self, name, notebook, assignment, **kwargs):
        try:
            solution_cell = self.find_solution_cell(name, notebook, assignment)
        except NoResultFound:
            solution_cell = self.add_solution_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(solution_cell, attr, kwargs[attr])
            self.db.commit()

        return solution_cell

    #### Submissions

    def add_submission(self, assignment, student, **kwargs):
        submission = SubmittedAssignment(
            assignment=self.find_assignment(assignment),
            student=self.find_student(student),
            **kwargs)

        for notebook in submission.assignment.notebooks:
            nb = SubmittedNotebook(notebook=notebook, assignment=submission)

            for grade_cell in notebook.grade_cells:
                grade = Grade(cell=grade_cell, notebook=nb)

            for solution_cell in notebook.solution_cells:
                comment = Comment(cell=solution_cell, notebook=nb)

        self.db.add(submission)
        try:
            self.db.commit()
        except IntegrityError as e:
            raise InvalidEntry(e.message)

        return submission

    def assignment_submissions(self, assignment):
        return self.db.query(SubmittedAssignment)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .filter(Assignment.name == assignment)\
            .all()

    def student_submissions(self, student):
        return self.db.query(SubmittedAssignment)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(Student.id == student)\
            .all()

    def find_submission(self, assignment, student):
        return self.db.query(SubmittedAssignment)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(Assignment.name == assignment, Student.id == student)\
            .one()

    def find_submission_notebook(self, name, assignment, student):
        return self.db.query(SubmittedNotebook)\
            .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
            .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(
                Notebook.name == name,
                Assignment.name == assignment,
                Student.id == student)\
            .one()

    def find_submission_notebook_by_id(self, notebook_id):
        return self.db.query(SubmittedNotebook).filter(SubmittedNotebook.id == notebook_id).one()

    def find_grade(self, name, notebook, assignment, student):
        return self.db.query(Grade)\
            .join(GradeCell, GradeCell.id == Grade.cell_id)\
            .join(SubmittedNotebook, SubmittedNotebook.id == Grade.notebook_id)\
            .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
            .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(
                GradeCell.name == name,
                Notebook.name == notebook,
                Assignment.name == assignment,
                Student.id == student)\
            .one()

    def find_grade_by_id(self, grade_id):
        return self.db.query(Grade).filter(Grade.id == grade_id).one()

    def find_comment(self, name, notebook, assignment, student):
        return self.db.query(Comment)\
            .join(SolutionCell, SolutionCell.id == Comment.cell_id)\
            .join(SubmittedNotebook, SubmittedNotebook.id == Comment.notebook_id)\
            .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
            .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(
                SolutionCell.name == name,
                Notebook.name == notebook,
                Assignment.name == assignment,
                Student.id == student)\
            .one()

    def find_comment_by_id(self, comment_id):
        return self.db.query(Comment).filter(Comment.id == comment_id).one()

    def update_or_create_submission(self, assignment, student, **kwargs):
        try:
            submission = self.find_submission(assignment, student)
        except NoResultFound:
            submission = self.add_submission(assignment, student, **kwargs)
        else:
            for attr in kwargs:
                setattr(submission, attr, kwargs[attr])
            self.db.commit()

        return submission
