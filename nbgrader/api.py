from __future__ import division

from . import utils

import datetime
import subprocess as sp

from sqlalchemy import (create_engine, ForeignKey, Column, String, Text,
                        DateTime, Interval, Float, Enum, UniqueConstraint,
                        Boolean)
from sqlalchemy.orm import (sessionmaker, scoped_session, relationship,
                            column_property, aliased)
from sqlalchemy.orm.exc import NoResultFound, FlushError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import and_, or_
from sqlalchemy import select, func, exists, case, literal_column, union_all
from sqlalchemy.ext.declarative import declared_attr
from uuid import uuid4
from .dbutil import _temp_alembic_ini

Base = declarative_base()


def new_uuid():
    return uuid4().hex


def get_alembic_version():
    with _temp_alembic_ini('sqlite:////tmp/gradebook.db') as alembic_ini:
        output = sp.check_output(['alembic', '-c', alembic_ini, 'heads'])
        head = output.decode().split("\n")[0].split(" ")[0]
        return head


class InvalidEntry(ValueError):
    pass


class MissingEntry(ValueError):
    pass

class Assignment(Base):
    """Database representation of the master/source version of an assignment."""

    __tablename__ = "assignment"

    #: Unique id of the assignment (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique human-readable name for the assignment, such as "Problem Set 1"
    name = Column(String(128), unique=True, nullable=False)

    #: (Optional) Duedate for the assignment in datetime format, with UTC timezone
    duedate = Column(DateTime())

    #: The course for this assignment
    course_id = Column(String(128), ForeignKey('course.id'), nullable=False)
    course = relationship("Course", back_populates="assignments")

    #: A collection of notebooks contained in this assignment, represented
    #: by :class:`~nbgrader.api.Notebook` objects
    notebooks = relationship("Notebook", backref="assignment", order_by="Notebook.name")

    #: A collection of submissions of this assignment, represented by
    #: :class:`~nbgrader.api.SubmittedAssignment` objects.
    submissions = relationship("SubmittedAssignment", backref="assignment")

    #: The number of submissions of this assignment
    num_submissions = None

    #: Maximum score achievable on this assignment, automatically calculated
    #: from the :attr:`~nbgrader.api.Notebook.max_score` of each notebook
    max_score = None

    #: Maximum coding score achievable on this assignment, automatically
    #: calculated from the :attr:`~nbgrader.api.Notebook.max_code_score` of
    #: each notebook
    max_code_score = None

    #: Maximum written score achievable on this assignment, automatically
    #: calculated from the :attr:`~nbgrader.api.Notebook.max_written_score` of
    #: each notebook
    max_written_score = None

    def __init__(self, name, duedate=None, course_id="default_course", **kwargs):
        self.name = name
        self.duedate = duedate
        self.course_id = course_id

    def to_dict(self):
        """Convert the assignment object to a JSON-friendly dictionary
        representation.

        """
        return {
            "id": self.id,
            "name": self.name,
            "duedate": self.duedate.isoformat() if self.duedate is not None else None,
            "num_submissions": self.num_submissions,
            "max_score": self.max_score,
            "max_code_score": self.max_code_score,
            "max_written_score": self.max_written_score,
            "max_task_score": self.max_written_score,
        }

    def __repr__(self):
        return "Assignment<{}>".format(self.name)


class Notebook(Base):
    """Database representation of the master/source version of a notebook."""

    __tablename__ = "notebook"
    __table_args__ = (UniqueConstraint('name', 'assignment_id'),)

    #: Unique id of the notebook (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique human-readable name for the notebook, such as "Problem 1". Note
    #: the uniqueness is only constrained within assignments (e.g. it is ok for
    #: two different assignments to both have notebooks called "Problem 1", but
    #: the same assignment cannot have two notebooks with the same name).
    name = Column(String(128), nullable=False)

    #: The :class:`~nbgrader.api.Assignment` object that this notebook is a
    #: part of
    assignment = None

    #: Unique id of :attr:`~nbgrader.api.Notebook.assignment`
    assignment_id = Column(String(32), ForeignKey('assignment.id'))

    #: The json string representation of the kernelspec for this notebook
    kernelspec = Column(String(1024), nullable=True)

    #: A collection of grade cells contained within this notebook, represented
    #: by :class:`~nbgrader.api.GradeCell` objects
    grade_cells = relationship("GradeCell", backref="grade_notebook")

    #: A collection of solution cells contained within this notebook, represented
    #: by :class:`~nbgrader.api.SolutionCell` objects
    solution_cells = relationship("SolutionCell", backref="solution_notebook")

    #: A collection of task cells contained within this notebook, represented
    #: by :class:`~nbgrader.api.TaskCell` objects
    task_cells = relationship("TaskCell", backref="task_notebook")

    #: A collection of source cells contained within this notebook, represented
    #: by :class:`~nbgrader.api.SourceCell` objects
    source_cells = relationship("SourceCell", backref="notebook")

    #: A collection of submitted versions of this notebook, represented by
    #: :class:`~nbgrader.api.SubmittedNotebook` objects
    submissions = relationship("SubmittedNotebook", backref="notebook")

    #: The number of submissions of this notebook
    num_submissions = None

    #: Maximum score achievable on this notebook, automatically calculated
    #: from the :attr:`~nbgrader.api.GradeCell.max_score` of each grade cell
    max_score = None

    #: Maximum coding score achievable on this notebook, automatically
    #: calculated from the :attr:`~nbgrader.api.GradeCell.max_score` and
    #: :attr:`~nbgrader.api.GradeCell.cell_type` of each grade cell
    max_code_score = None

    #: Maximum written score achievable on this notebook, automatically
    #: calculated from the :attr:`~nbgrader.api.GradeCell.max_score` and
    #: :attr:`~nbgrader.api.GradeCell.cell_type` of each grade cell
    max_written_score = None

    #: Whether there are any submitted versions of this notebook that need to
    #: be manually graded, automatically determined from the
    #: :attr:`~nbgrader.api.SubmittedNotebook.needs_manual_grade` attribute of
    #: each submitted notebook
    needs_manual_grade = None

    def to_dict(self):
        """Convert the notebook object to a JSON-friendly dictionary
        representation.

        """
        return {
            "id": self.id,
            "name": self.name,
            "num_submissions": self.num_submissions,
            "max_score": self.max_score,
            "max_code_score": self.max_code_score,
            "max_written_score": self.max_written_score,
            "max_task_score": self.max_task_score,
            "needs_manual_grade": self.needs_manual_grade
        }

    def __repr__(self):
        return "Notebook<{}/{}>".format(self.assignment.name, self.name)


class BaseCell(Base):
    """Database representation of a cell. It is meant as a base class for cells where additional behavior is added through mixin classes."""

    __tablename__ = "base_cell"
    __table_args__ = (UniqueConstraint('name', 'notebook_id', 'type'),)

    #: Unique id of the grade cell (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique human-readable name of the grade cell. This need only be unique
    #: within the notebook, not across notebooks.
    name = Column(String(128), nullable=False)

    #: The :class:`~nbgrader.api.Notebook` that this grade cell is contained in
    @property
    def notebook(self):
        if hasattr(self, 'task_notebook'):
            return self.task_notebook
        elif hasattr(self, 'solution_notebook'):
            return self.solution_notebook
        elif hasattr(self, 'grade_notebook'):
            return self.grade_notebook

    @notebook.setter
    def notebook(self, value):
        if hasattr(self, 'task_notebook'):
            self.task_notebook = value
        elif hasattr(self, 'solution_notebook'):
            self.solution_notebook = value
        elif hasattr(self, 'grade_notebook'):
            self.grade_notebook = value

    #: Unique id of the :attr:`~nbgrader.api.GradeCell.notebook`
    notebook_id = Column(String(32), ForeignKey('notebook.id'), nullable=False)

    #: The assignment that this cell is contained within, represented by a
    #: :class:`~nbgrader.api.Assignment` object

    @property
    def assignment(self):
        return self.notebook.assignment

    def __repr__(self):
        return "GradeCell<{}/{}/{}>".format(
            self.assignment.name, self.notebook.name, self.name)

    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'BaseCell',
        'polymorphic_on': type
    }


class GradedMixin():
    """Mixin class providing the reference to a grade and the data members relevant for graded cells."""
    #: Maximum score that can be assigned to this grade cell
    @declared_attr
    def max_score(cls):
        return Column(Float(), nullable=False)

    #: The cell type, either "code" or "markdown"
    @declared_attr
    def cell_type(cls):
        return Column(Enum("code", "markdown", name="grade_cell_type"), nullable=False)

    #: A collection of  assigned to submitted versions of this grade cell,
    #: represented by :class:`~nbgrader.api.Grade` objects
    @declared_attr
    def grades(cls):
        return relationship("Grade", backref="graded_" + cls.__name__)


class GradeCell(BaseCell, GradedMixin):
    """Database representation of the master/source version of a grade cell."""

    __tablename__ = "grade_cells"

    #: Unique id of the cell (automatically generated from BaseCell)
    id = Column(String(32), ForeignKey('base_cell.id'), primary_key=True)

    def to_dict(self):
        """Convert the grade cell object to a JSON-friendly dictionary
        representation. Note that this includes keys for ``notebook`` and
        ``assignment`` which correspond to the names of the notebook and
        assignment, not the objects themselves.

        """
        return {
            "id": self.id,
            "name": self.name,
            "max_score": self.max_score,
            "cell_type": self.cell_type,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name
        }

    def __repr__(self):
        return "GradeCell<{}/{}/{}>".format(
            self.assignment.name, self.notebook.name, self.name)

    __mapper_args__ = {
        'polymorphic_identity': 'GradeCell',
    }


class CommentedMixin():
    """Mixin class providing the reference to comments for commented cells."""

    #: A collection of comments assigned to submitted versions of this grade cell,
    #: represented by :class:`~nbgrader.api.Comment` objects
    @declared_attr
    def comments(cls):
        return relationship("Comment", backref="commented_" + cls.__name__)


class SolutionCell(BaseCell, CommentedMixin):
    __tablename__ = "solution_cells"
    #: Unique id of the cell (automatically generated from BaseCell)
    id = Column(String(32), ForeignKey('base_cell.id'), primary_key=True)

    def to_dict(self):
        """Convert the solution cell object to a JSON-friendly dictionary
        representation. Note that this includes keys for ``notebook`` and
        ``assignment`` which correspond to the names of the notebook and
        assignment, not the objects themselves.

        """
        return {
            "id": self.id,
            "name": self.name,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name
        }

    def __repr__(self):
        return "SolutionCell<{}/{}/{}>".format(
            self.assignment.name, self.notebook.name, self.name)

    __mapper_args__ = {
        'polymorphic_identity': 'SolutionCell',
    }


class TaskCell(BaseCell, GradedMixin, CommentedMixin):
    """Database representation of a task cell."""

    __tablename__ = "task_cells"

    #: Unique id of the cell (automatically generated from BaseCell)
    id = Column(String(32), ForeignKey('base_cell.id'), primary_key=True)

    def to_dict(self):
        """Convert the task cell object to a JSON-friendly dictionary
        representation. Note that this includes keys for ``notebook`` and
        ``assignment`` which correspond to the names of the notebook and
        assignment, not the objects themselves.

        """
        return {
            "id": self.id,
            "name": self.name,
            "max_score": self.max_score,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name
        }

    def __repr__(self):
        return "SolutionCell<{}/{}/{}>".format(
            self.assignment.name, self.notebook.name, self.name)

    __mapper_args__ = {'polymorphic_identity': 'TaskCell'}


class SourceCell(Base):
    __tablename__ = "source_cell"
    __table_args__ = (UniqueConstraint('name', 'notebook_id'),)

    #: Unique id of the source cell (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique human-readable name of the source cell. This need only be unique
    #: within the notebook, not across notebooks.
    name = Column(String(128), nullable=False)

    #: The cell type, either "code" or "markdown"
    cell_type = Column(Enum("code", "markdown", name="source_cell_type"), nullable=False)

    #: Whether the cell is locked (e.g. the source saved in the database should
    #: be used to overwrite the source of students' cells)
    locked = Column(Boolean, default=False, nullable=False)

    #: The source code or text of the cell
    source = Column(Text())

    #: A checksum of the cell contents. This should usually be computed
    #: using :func:`nbgrader.utils.compute_checksum`
    checksum = Column(String(128))

    #: The :class:`~nbgrader.api.Notebook` that this source cell is contained in
    notebook = None

    #: Unique id of the :attr:`~nbgrader.api.SourceCell.notebook`
    notebook_id = Column(String(32), ForeignKey('notebook.id'))

    #: The assignment that this cell is contained within, represented by a
    #: :class:`~nbgrader.api.Assignment` object
    assignment = association_proxy("notebook", "assignment")

    def to_dict(self):
        """Convert the source cell object to a JSON-friendly dictionary
        representation. Note that this includes keys for ``notebook`` and
        ``assignment`` which correspond to the names of the notebook and
        assignment, not the objects themselves.

        """
        return {
            "id": self.id,
            "name": self.name,
            "cell_type": self.cell_type,
            "locked": self.locked,
            "source": self.source,
            "checksum": self.checksum,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name
        }

    def __repr__(self):
        return "SourceCell<{}/{}/{}>".format(
            self.assignment.name, self.notebook.name, self.name)


class Student(Base):
    """Database representation of a student."""

    __tablename__ = "student"

    #: Unique id of the student. This could be a student ID, a username, an
    #: email address, etc., so long as it is unique.
    id = Column(String(128), primary_key=True, nullable=False)

    #: (Optional) The first name of the student
    first_name = Column(String(128))

    #: (Optional) The last name of the student
    last_name = Column(String(128))

    #: (Optional) The student's email address, if the :attr:`~nbgrader.api.Student.id`
    #: does not correspond to an email address
    email = Column(String(128))

    #: A collection of assignments submitted by the student, represented as
    #: :class:`~nbgrader.api.SubmittedAssignment` objects
    submissions = relationship("SubmittedAssignment", backref="student")

    #: The overall score of the student across all assignments, computed
    #: automatically from the :attr:`~nbgrader.api.SubmittedAssignment.score`
    #: of each submitted assignment.
    score = None

    #: The maximum possible score the student could achieve across all assignments,
    #: computed automatically from the :attr:`~nbgrader.api.Assignment.max_score`
    #: of each assignment.
    max_score = None

    #: The LMS user ID, this is mainly for identifying students in your LMS system
    #: and was added so teachers and TA's can easily send grades to a LMS such as Canvas and Blackboard.
    lms_user_id = Column(String(128), nullable=True)

    def to_dict(self):
        """Convert the student object to a JSON-friendly dictionary
        representation.

        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "score": self.score,
            "max_score": self.max_score,
            "lms_user_id": self.lms_user_id
        }

    def __repr__(self):
        return "Student<{}>".format(self.id)


class SubmittedAssignment(Base):
    """Database representation of an assignment submitted by a student."""

    __tablename__ = "submitted_assignment"
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id'),)

    #: Unique id of the submitted assignment (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Name of the assignment, inherited from :class:`~nbgrader.api.Assignment`
    name = association_proxy("assignment", "name")

    #: The master version of this assignment, represented by a
    #: :class:`~nbgrader.api.Assignment` object
    assignment = None

    #: Unique id of :attr:`~nbgrader.api.SubmittedAssignment.assignment`
    assignment_id = Column(String(32), ForeignKey('assignment.id'))

    #: The student who submitted this assignment, represented by a
    #: :class:`~nbgrader.api.Student` object
    student = None

    #: Unique id of :attr:`~nbgrader.api.SubmittedAssignment.student`
    student_id = Column(String(128), ForeignKey('student.id'))

    #: (Optional) The date and time that the assignment was submitted, in date
    #: time format with a UTC timezone
    timestamp = Column(DateTime())

    #: (Optional) An extension given to the student for this assignment, in
    #: time delta format
    extension = Column(Interval())

    #: A collection of notebooks contained within this submitted assignment,
    #: represented by :class:`~nbgrader.api.SubmittedNotebook` objects
    notebooks = relationship("SubmittedNotebook", backref="assignment")

    #: The score assigned to this assignment, automatically calculated from the
    #: :attr:`~nbgrader.api.SubmittedNotebook.score` of each notebook within
    #: this submitted assignment.
    score = None

    #: The maximum possible score of this assignment, inherited from
    #: :class:`~nbgrader.api.Assignment`
    max_score = None

    #: The code score assigned to this assignment, automatically calculated from
    #: the :attr:`~nbgrader.api.SubmittedNotebook.code_score` of each notebook
    #: within this submitted assignment.
    code_score = None

    #: The maximum possible code score of this assignment, inherited from
    #: :class:`~nbgrader.api.Assignment`
    max_code_score = None

    #: The written score assigned to this assignment, automatically calculated
    #: from the :attr:`~nbgrader.api.SubmittedNotebook.written_score` of each
    #: notebook within this submitted assignment.
    written_score = None

    #: The maximum possible written score of this assignment, inherited from
    #: :class:`~nbgrader.api.Assignment`
    max_written_score = None

    #: The task score assigned to this assignment, automatically calculated
    #: from the :attr:`~nbgrader.api.SubmittedNotebook.task_score` of each
    #: notebook within this submitted assignment.
    task_score = None

    #: The maximum possible task score of this assignment, inherited from
    #: :class:`~nbgrader.api.Assignment`
    max_task_score = None
    #: Whether this assignment has parts that need to be manually graded,
    #: automatically determined from the :attr:`~nbgrader.api.SubmittedNotebook.needs_manual_grade`
    #: attribute of each notebook.
    needs_manual_grade = None

    #: The penalty (>= 0) given for submitting the assignment late.
    #: Automatically determined from the
    #: :attr:`~nbgrader.api.SubmittedNotebook.late_submission_penalty`
    #: attribute of each notebook.
    late_submission_penalty = None

    @property
    def duedate(self):
        """The duedate of this student's assignment, which includes any extension
        given, if applicable, and which is just the regular assignment duedate
        otherwise.

        """
        orig_duedate = self.assignment.duedate
        if self.extension is not None:
            return orig_duedate + self.extension
        else:
            return orig_duedate

    @property
    def total_seconds_late(self):
        """The number of seconds that this assignment was turned in past the
        duedate (including extensions, if any). If the assignment was turned in
        before the deadline, this value will just be zero.

        """
        if self.timestamp is None or self.duedate is None:
            return 0
        else:
            return max(0, (self.timestamp - self.duedate).total_seconds())

    def to_dict(self):
        """Convert the submitted assignment object to a JSON-friendly dictionary
        representation. Note that this includes a ``student`` key which is the
        unique id of the student, not the object itself.

        """
        return {
            "id": self.id,
            "name": self.name,
            "student": self.student.id,
            "first_name": self.student.first_name,
            "last_name": self.student.last_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "score": self.score,
            "max_score": self.max_score,
            "code_score": self.code_score,
            "max_code_score": self.max_code_score,
            "written_score": self.written_score,
            "max_written_score": self.max_written_score,
            "task_score": self.task_score,
            "max_task_score": self.max_task_score,
            "needs_manual_grade": self.needs_manual_grade
        }

    def __repr__(self):
        return "SubmittedAssignment<{} for {}>".format(self.name, self.student.id)


class SubmittedNotebook(Base):
    """Database representation of a notebook submitted by a student."""

    __tablename__ = "submitted_notebook"
    __table_args__ = (UniqueConstraint('notebook_id', 'assignment_id'),)

    #: Unique id of the submitted notebook (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Name of the notebook, inherited from :class:`~nbgrader.api.Notebook`
    name = association_proxy("notebook", "name")

    #: The submitted assignment this notebook is a part of, represented by a
    #: :class:`~nbgrader.api.SubmittedAssignment` object
    assignment = None

    #: Unique id of :attr:`~nbgrader.api.SubmittedNotebook.assignment`
    assignment_id = Column(String(32), ForeignKey('submitted_assignment.id'))

    #: The master version of this notebook, represented by a
    #: :class:`~nbgrader.api.Notebook` object
    notebook = None

    #: Unique id of :attr:`~nbgrader.api.SubmittedNotebook.notebook`
    notebook_id = Column(String(32), ForeignKey('notebook.id'))

    #: Collection of associated with this submitted notebook, represented
    #: by :class:`~nbgrader.api.Grade` objects
    grades = relationship("Grade", backref="notebook")

    #: Collection of comments associated with this submitted notebook, represented
    #: by :class:`~nbgrader.api.Comment` objects
    comments = relationship("Comment", backref="notebook")

    #: The student who submitted this notebook, represented by a
    #: :class:`~nbgrader.api.Student` object
    student = association_proxy('assignment', 'student')

    #: Whether this assignment has been flagged by a human grader
    flagged = Column(Boolean, default=False)

    #: The score assigned to this notebook, automatically calculated from the
    #: :attr:`~nbgrader.api.Grade.score` of each grade cell within
    #: this submitted notebook.
    score = None

    #: The maximum possible score of this notebook, inherited from
    #: :class:`~nbgrader.api.Notebook`
    max_score = None

    #: The code score assigned to this notebook, automatically calculated from
    #: the :attr:`~nbgrader.api.Grade.score` and :attr:`~nbgrader.api.GradeCell.cell_type`
    #: of each grade within this submitted notebook.
    code_score = None

    #: The maximum possible code score of this notebook, inherited from
    #: :class:`~nbgrader.api.Notebook`
    max_code_score = None

    #: The written score assigned to this notebook, automatically calculated from
    #: the :attr:`~nbgrader.api.Grade.score` and :attr:`~nbgrader.api.GradeCell.cell_type`
    #: of each grade within this submitted notebook.
    written_score = None

    #: The maximum possible written score of this notebook, inherited from
    #: :class:`~nbgrader.api.Notebook`
    max_written_score = None

    #: Whether this notebook has parts that need to be manually graded,
    #: automatically determined from the :attr:`~nbgrader.api.Grade.needs_manual_grade`
    #: attribute of each grade.
    needs_manual_grade = None

    #: Whether this notebook contains autograder tests that failed to pass,
    #: automatically determined from the :attr:`~nbgrader.api.Grade.failed_tests`
    #: attribute of each grade.
    failed_tests = None

    #: The penalty (>= 0) given for submitting the assignment late. Updated
    #: by the :class:`~nbgrader.plugins.LateSubmissionPlugin`.
    late_submission_penalty = Column(Float(0))

    def to_dict(self):
        """Convert the submitted notebook object to a JSON-friendly dictionary
        representation. Note that this includes a key for ``student`` which is
        the unique id of the student, not the actual student object.

        """
        return {
            "id": self.id,
            "name": self.name,
            "student": self.student.id,
            "last_name": self.student.last_name,
            "first_name": self.student.first_name,
            "score": self.score,
            "max_score": self.max_score,
            "code_score": self.code_score,
            "max_code_score": self.max_code_score,
            "written_score": self.written_score,
            "max_written_score": self.max_written_score,
            "task_score": self.task_score,
            "max_task_score": self.max_task_score,
            "needs_manual_grade": self.needs_manual_grade,
            "failed_tests": self.failed_tests,
            "flagged": self.flagged,
        }

    def __repr__(self):
        return "SubmittedNotebook<{}/{} for {}>".format(
            self.assignment.name, self.name, self.student.id)


class Grade(Base):
    """Database representation of a grade assigned to the submitted version of
    a grade cell.

    """

    __tablename__ = "grade"
    __table_args__ = (UniqueConstraint('cell_id', 'notebook_id'),)

    #: Unique id of the grade (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique name of the grade cell, inherited from :class:`~nbgrader.api.GradeCell`
    taskcell_name = association_proxy('graded_TaskCell', 'name')
    gradecell_name = association_proxy('graded_GradeCell', 'name')

    @property
    def name(self):
        if self.taskcell_name:
            return self.taskcell_name
        else:
            return self.gradecell_name

    #: The submitted assignment that this grade is contained in, represented by
    #: a :class:`~nbgrader.api.SubmittedAssignment` object
    assignment = association_proxy('notebook', 'assignment')

    #: The submitted notebook that this grade is assigned to, represented by a
    #: :class:`~nbgrader.api.SubmittedNotebook` object
    notebook = None

    #: Unique id of :attr:`~nbgrader.api.Grade.notebook`
    notebook_id = Column(String(32), ForeignKey('submitted_notebook.id'))

    #: The master version of the cell this grade is assigned to, represented by
    #: a :class:`~nbgrader.api.GradeCell` object.

    graded_GradeCell = None
    graded_TaskCell = None

    @property
    def cell(self):
        if self.graded_TaskCell:
            return self.graded_TaskCell
        elif self.graded_GradeCell:
            return self.graded_GradeCell
        else:
            raise ValueError(self)

    @cell.setter
    def cell(self, value):
        if value.__class__.__name__ == "TaskCell":
            self.graded_TaskCell = value
        elif value.__class__.__name__ == "GradeCell":
            self.graded_GradeCell = value
        else:
            raise ValueError(value)

    #: Unique id of :attr:`~nbgrader.api.Grade.cell`
    cell_id = Column(String(32), ForeignKey('base_cell.id'))

    #: The type of cell this grade corresponds to, inherited from
    #: :class:`~nbgrader.api.GradeCell`

    #: The student who this grade is assigned to, represented by a
    #: :class:`~nbgrader.api.Student` object
    student = association_proxy('notebook', 'student')

    #: Score assigned by the autograder
    auto_score = Column(Float())

    #: Score assigned by a human grader
    manual_score = Column(Float())

    #: Extra credit assigned by a human grader
    extra_credit = Column(Float())

    #: Whether a score needs to be assigned manually. This is True by default.
    needs_manual_grade = Column(Boolean, default=True, nullable=False)

    #: The overall score, computed automatically from the
    #: :attr:`~nbgrader.api.Grade.auto_score` and :attr:`~nbgrader.api.Grade.manual_score`
    #: values. If neither are set, the score is zero. If both are set, then the
    #: manual score takes precedence. If only one is set, then that value is used
    #: for the score.
    score = column_property(case(
        [
            (manual_score != None, manual_score + case([(extra_credit != None, extra_credit)], else_=literal_column("0.0"))),
            (auto_score != None, auto_score + case([(extra_credit != None, extra_credit)], else_=literal_column("0.0")))
        ],
        else_=literal_column("0.0")
    ))

    #: The maximum possible score that can be assigned, inherited from
    #: :class:`~nbgrader.api.GradeCell`
    max_score_gradecell = None
    max_score_taskcell = None

    @property
    def max_score(self):
        if self.max_score_taskcell:
            return self.max_score_taskcell
        else:
            return self.max_score_gradecell

    #: Whether the autograded score is a result of failed autograder tests. This
    #: is True if the autograder score is zero and the cell type is "code", and
    #: otherwise False.
    failed_tests = None

    def to_dict(self):
        """Convert the grade object to a JSON-friendly dictionary representation.
        Note that this includes keys for ``notebook`` and ``assignment`` which
        correspond to the name of the notebook and assignment, not the actual
        objects. It also includes a key for ``student`` which corresponds to the
        unique id of the student, not the actual student object.

        """
        return {
            "id": self.id,
            "name": self.name,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name,
            "student": self.student.id,
            "auto_score": self.auto_score,
            "manual_score": self.manual_score,
            "extra_credit": self.extra_credit,
            "max_score": self.max_score,
            "needs_manual_grade": self.needs_manual_grade,
            "failed_tests": self.failed_tests,
            "cell_type": self.cell_type
        }

    def __repr__(self):
        return "Grade<{}/{}/{} for {}>".format(
            self.assignment.name, self.notebook.name, self.name, self.student.id)


class Comment(Base):
    """Database representation of a comment on a cell in a submitted notebook."""

    __tablename__ = "comment"
    __table_args__ = (UniqueConstraint('cell_id', 'notebook_id'),)

    #: Unique id of the comment (automatically generated)
    id = Column(String(32), primary_key=True, default=new_uuid)

    #: Unique name of the solution cell, inherited from :class:`~nbgrader.api.SolutionCell`
    name_taskcell = association_proxy('commented_TaskCell', 'name')
    name_solutioncell = association_proxy('commented_SolutionCell', 'name')

    @property
    def name(self):
        if self.commented_TaskCell:
            return self.name_taskcell
        else:
            return self.name_solutioncell

    #: The submitted assignment that this comment is contained in, represented by
    #: a :class:`~nbgrader.api.SubmittedAssignment` object
    assignment = association_proxy('notebook', 'assignment')

    #: The submitted notebook that this comment is assigned to, represented by a
    #: :class:`~nbgrader.api.SubmittedNotebook` object
    notebook = None

    #: Unique id of :attr:`~nbgrader.api.Comment.notebook`
    notebook_id = Column(String(32), ForeignKey('submitted_notebook.id'))

    #: The master version of the cell this comment is assigned to, represented by
    #: a :class:`~nbgrader.api.SolutionCell` object.
    commented_TaskCell = None
    commented_SolutionCell = None

    @property
    def cell(self):
        if self.commented_TaskCell:
            return self.commented_TaskCell
        elif self.commented_SolutionCell:
            return self.commented_SolutionCell
        else:
            raise ValueError(self)

    @cell.setter
    def cell(self, value):
        if value.__class__.__name__ == "TaskCell":
            self.commented_TaskCell = value
        elif value.__class__.__name__ == "SolutionCell":
            self.commented_SolutionCell = value
        else:
            raise ValueError(value)

    #: Unique id of :attr:`~nbgrader.api.Comment.cell`
    cell_id = Column(String(32), ForeignKey('base_cell.id'))

    #: The student who this comment is assigned to, represented by a
    #: :class:`~nbgrader.api.Student` object
    student = association_proxy('notebook', 'student')

    #: A comment which is automatically assigned by the autograder
    auto_comment = Column(Text())

    #: A comment which is assigned manually
    manual_comment = Column(Text())

    #: The overall comment, computed automatically from the
    #: :attr:`~nbgrader.api.Comment.auto_comment` and
    #: :attr:`~nbgrader.api.Comment.manual_comment` values. If neither are set,
    #: the comment is None. If both are set, then the manual comment
    #: takes precedence. If only one is set, then that value is used for the
    #: comment.
    comment = column_property(case(
        [
            (manual_comment != None, manual_comment),
            (auto_comment != None, auto_comment)
        ],
        else_=None
    ))

    def to_dict(self):
        """Convert the comment object to a JSON-friendly dictionary representation.
        Note that this includes keys for ``notebook`` and ``assignment`` which
        correspond to the name of the notebook and assignment, not the actual
        objects. It also includes a key for ``student`` which corresponds to the
        unique id of the student, not the actual student object.

        """
        return {
            "id": self.id,
            "name": self.name,
            "notebook": self.notebook.name,
            "assignment": self.assignment.name,
            "student": self.student.id,
            "auto_comment": self.auto_comment,
            "manual_comment": self.manual_comment
        }

    def __repr__(self):
        return "Comment<{}/{}/{} for {}>".format(
            self.assignment.name, self.notebook.name, self.name, self.student.id)

class Course(Base):
    """Table to store the courses"""

    __tablename__ = "course"

    id = Column(String(128), unique=True, primary_key=True, nullable=False)
    assignments = relationship("Assignment", back_populates="course")

    def __repr__(self):
        return "Course<{}>".format(self.id)

## Needs manual grade

SubmittedNotebook.needs_manual_grade = column_property(
    exists().where(and_(
        Grade.notebook_id == SubmittedNotebook.id,
        Grade.needs_manual_grade))
    .correlate_except(Grade), deferred=True)

SubmittedAssignment.needs_manual_grade = column_property(
    exists().where(and_(
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id,
        Grade.needs_manual_grade))
    .correlate_except(Grade), deferred=True)

Notebook.needs_manual_grade = column_property(
    exists().where(and_(
        Notebook.id == SubmittedNotebook.notebook_id,
        Grade.notebook_id == SubmittedNotebook.id,
        Grade.needs_manual_grade))
    .correlate_except(Grade), deferred=True)


# Overall scores

SubmittedNotebook.score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(Grade.notebook_id == SubmittedNotebook.id)
    .correlate_except(Grade), deferred=True)

SubmittedAssignment.score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id))
    .correlate_except(Grade), deferred=True)

Student.score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        SubmittedAssignment.student_id == Student.id,
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id))
    .correlate_except(Grade), deferred=True)


# Overall max scores

Grade.max_score_gradecell = column_property(
    select([func.coalesce(GradeCell.max_score, 0.0)])
    .select_from(GradeCell)
    .where(Grade.cell_id == GradeCell.id)
    .correlate_except(GradeCell), deferred=True)

Grade.max_score_taskcell = column_property(
    select([func.coalesce(TaskCell.max_score, 0.0)])
    .select_from(TaskCell)
    .where(Grade.cell_id == TaskCell.id)
    .correlate_except(TaskCell), deferred=True)
# a grade is either from a grade cell or a task cell , so only one will not be none
Grade.max_score = column_property(func.coalesce(Grade.max_score_gradecell, Grade.max_score_taskcell, 0.0), deferred=True)

# try defining the cell_type_**** as athe result of a search as for the max_score
# and not through the relationship

Grade.cell_type_from_taskcell = column_property(
    select([TaskCell.cell_type])
    .select_from(TaskCell)
    .where(Grade.cell_id == TaskCell.id)
    .correlate_except(TaskCell), deferred=True)

Grade.cell_type_from_gradecell = column_property(
    select([GradeCell.cell_type])
    .select_from(GradeCell)
    .where(Grade.cell_id == GradeCell.id)
    .correlate_except(GradeCell), deferred=True)

Grade.cell_type = column_property(
    select([func.coalesce(Grade.cell_type_from_gradecell, Grade.cell_type_from_taskcell)])
)


Notebook.max_score_gradecell = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
        .select_from(GradeCell)
        .where(GradeCell.notebook_id == Notebook.id)
        .correlate_except(GradeCell), deferred=True)

Notebook.max_score_taskcell = column_property(
    select([func.coalesce(func.sum(TaskCell.max_score), 0.0)])
        .select_from(TaskCell)
        .where(TaskCell.notebook_id == Notebook.id)
        .correlate_except(TaskCell), deferred=True)

Notebook.max_score = column_property(
    Notebook.max_score_gradecell + Notebook.max_score_taskcell
)

SubmittedNotebook.max_score = column_property(
    select([Notebook.max_score])
    .where(SubmittedNotebook.notebook_id == Notebook.id)
    .correlate_except(Notebook), deferred=True)

Assignment.max_score_gradecell = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
    .select_from(GradeCell)
    .where(and_(
        Notebook.assignment_id == Assignment.id,
        GradeCell.notebook_id == Notebook.id))
    .correlate_except(GradeCell), deferred=True)

Assignment.max_score_taskcell = column_property(
    select([func.coalesce(func.sum(TaskCell.max_score), 0.0)])
    .select_from(TaskCell)
    .where(and_(
        Notebook.assignment_id == Assignment.id,
        TaskCell.notebook_id == Notebook.id))
    .correlate_except(TaskCell), deferred=True)

Assignment.max_score = column_property(
    Assignment.max_score_gradecell + Assignment.max_score_taskcell
)


SubmittedAssignment.max_score = column_property(
    select([Assignment.max_score])
    .where(SubmittedAssignment.assignment_id == Assignment.id)
    .correlate_except(Assignment), deferred=True)

Student.max_score = column_property(
    select([func.coalesce(func.sum(Assignment.max_score), 0.0)])
    .correlate_except(Assignment), deferred=True)


# Written scores

SubmittedNotebook.written_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        Grade.notebook_id == SubmittedNotebook.id,
        GradeCell.id == Grade.cell_id,
        GradeCell.cell_type == "markdown"))
    .correlate_except(Grade), deferred=True)

SubmittedAssignment.written_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id,
        GradeCell.id == Grade.cell_id,
        GradeCell.cell_type == "markdown"))
    .correlate_except(Grade), deferred=True)


# Written max scores

Notebook.max_written_score = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
    .select_from(GradeCell)
    .where(and_(
        GradeCell.notebook_id == Notebook.id,
        GradeCell.cell_type == "markdown"))
    .correlate_except(GradeCell), deferred=True)

SubmittedNotebook.max_written_score = column_property(
    select([Notebook.max_written_score])
    .where(Notebook.id == SubmittedNotebook.notebook_id)
    .correlate_except(Notebook), deferred=True)

Assignment.max_written_score = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
    .select_from(GradeCell)
    .where(and_(
        Notebook.assignment_id == Assignment.id,
        GradeCell.notebook_id == Notebook.id,
        GradeCell.cell_type == "markdown"))
    .correlate_except(GradeCell), deferred=True)

SubmittedAssignment.max_written_score = column_property(
    select([Assignment.max_written_score])
    .where(Assignment.id == SubmittedAssignment.assignment_id)
    .correlate_except(Assignment), deferred=True)


# Code scores

SubmittedNotebook.code_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        Grade.notebook_id == SubmittedNotebook.id,
        GradeCell.id == Grade.cell_id,
        GradeCell.cell_type == "code"))
    .correlate_except(Grade), deferred=True)

SubmittedAssignment.code_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id,
        GradeCell.id == Grade.cell_id,
        GradeCell.cell_type == "code"))
    .correlate_except(Grade), deferred=True)


# Code max scores

Notebook.max_code_score = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
        .select_from(GradeCell)
        .where(and_(
            GradeCell.notebook_id == Notebook.id,
            GradeCell.cell_type == "code"))
        .correlate_except(GradeCell), deferred=True)

SubmittedNotebook.max_code_score = column_property(
    select([Notebook.max_code_score])
    .where(Notebook.id == SubmittedNotebook.notebook_id)
    .correlate_except(Notebook), deferred=True)

Assignment.max_code_score = column_property(
    select([func.coalesce(func.sum(GradeCell.max_score), 0.0)])
    .select_from(GradeCell)
    .where(and_(
        Notebook.assignment_id == Assignment.id,
        GradeCell.notebook_id == Notebook.id,
        GradeCell.cell_type == "code"))
    .correlate_except(GradeCell), deferred=True)

SubmittedAssignment.max_code_score = column_property(
    select([Assignment.max_code_score])
    .where(Assignment.id == SubmittedAssignment.assignment_id)
    .correlate_except(Assignment), deferred=True)

# task score

SubmittedNotebook.task_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        Grade.notebook_id == SubmittedNotebook.id,
        TaskCell.id == Grade.cell_id,
        TaskCell.cell_type == "markdown"))
    .correlate_except(Grade), deferred=True)

SubmittedAssignment.task_score = column_property(
    select([func.coalesce(func.sum(Grade.score), 0.0)])
    .where(and_(
        SubmittedNotebook.assignment_id == SubmittedAssignment.id,
        Grade.notebook_id == SubmittedNotebook.id,
        TaskCell.id == Grade.cell_id,
        TaskCell.cell_type == "markdown"))
    .correlate_except(Grade), deferred=True)


# task max scores

Notebook.max_task_score = column_property(
    select([func.coalesce(func.sum(TaskCell.max_score), 0.0)])
    .select_from(TaskCell)
    .where(and_(
        TaskCell.notebook_id == Notebook.id,
        TaskCell.cell_type == "markdown"))
    .correlate_except(TaskCell), deferred=True)

SubmittedNotebook.max_task_score = column_property(
    select([Notebook.max_task_score])
    .where(Notebook.id == SubmittedNotebook.notebook_id)
    .correlate_except(Notebook), deferred=True)

Assignment.max_task_score = column_property(
    select([func.coalesce(func.sum(TaskCell.max_score), 0.0)])
    .select_from(TaskCell)
    .where(and_(
        Notebook.assignment_id == Assignment.id,
        TaskCell.notebook_id == Notebook.id,
        TaskCell.cell_type == "markdown"))
    .correlate_except(TaskCell), deferred=True)

SubmittedAssignment.max_task_score = column_property(
    select([func.coalesce(Assignment.max_task_score, 0.0)])
)

# Number of submissions

Assignment.num_submissions = column_property(
    select([func.count(SubmittedAssignment.id)])
    .where(SubmittedAssignment.assignment_id == Assignment.id)
    .correlate_except(SubmittedAssignment), deferred=True)

Notebook.num_submissions = column_property(
    select([func.count(SubmittedNotebook.id)])
    .where(SubmittedNotebook.notebook_id == Notebook.id)
    .correlate_except(SubmittedNotebook), deferred=True)


# Cell type

Grade.cell_type_gradecell = column_property(
    select([GradeCell.cell_type])
    .select_from(GradeCell)
    .where(Grade.cell_id == GradeCell.id)
    .correlate_except(GradeCell), deferred=True)

Grade.cell_type_taskcell = column_property(
    select([TaskCell.cell_type])
    .select_from(TaskCell)
    .where(Grade.cell_id == TaskCell.id)
    .correlate_except(TaskCell), deferred=True)


# Failed tests

Grade.failed_tests = column_property(
    (Grade.cell_type_gradecell != None) & ((Grade.auto_score < Grade.max_score_gradecell) & (Grade.cell_type_gradecell == "code"))
)

SubmittedNotebook.failed_tests = column_property(
    exists().where(and_(
        Grade.notebook_id == SubmittedNotebook.id,
        Grade.failed_tests))
    .correlate_except(Grade), deferred=True)


# Late penalties

SubmittedAssignment.late_submission_penalty = column_property(
    select([func.coalesce(func.sum(SubmittedNotebook.late_submission_penalty), 0.0)])
    .where(SubmittedNotebook.assignment_id == SubmittedAssignment.id)
    .correlate_except(SubmittedNotebook), deferred=True)


class Gradebook(object):
    """The gradebook object to interface with the database holding
    nbgrader grades.

    """

    def __init__(self, db_url, course_id="default_course", authenticator=None):
        """Initialize the connection to the database.

        Parameters
        ----------
        db_url : string
            The URL to the database, e.g. ``sqlite:///grades.db``
        course_id : string, optional
            identifier of the course necessary for supporting multiple classes
            default course_id is '' to be consistent with :class:~`nbgrader.apps.api.NbGraderAPI`
        authenticator : :class:~`nbgrader.auth.BaseAuthenticator`
            An authenticator instance for communicating with an external
            database.

        """
        # create the connection to the database
        self.engine = create_engine(db_url, echo=False)
        self.db = scoped_session(sessionmaker(autoflush=True, bind=self.engine))

        # this creates all the tables in the database if they don't already exist
        db_exists = len(self.engine.table_names()) > 0
        Base.metadata.create_all(bind=self.engine)

        # set the alembic version if it doesn't exist
        if not db_exists:
            alembic_version = get_alembic_version()
            self.db.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);")
            self.db.execute("INSERT INTO alembic_version (version_num) VALUES ('{}');".format(alembic_version))
            self.db.commit()

        self.check_course(course_id=course_id)
        self.course_id = course_id
        self.authenticator = authenticator

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """Close the connection to the database.

        It is important to call this method after you are done using the
        gradebook. In particular, if you create multiple instances of the
        gradebook without closing them, you may run into errors where there
        are too many open connections to the database.

        """
        self.db.remove()
        self.engine.dispose()

    def check_course(self, course_id="default_course", **kwargs):
        """Set the course id

        Parameters
        ----------
        course_id : string
            The unique id of the course
        `**kwargs` : dict
            other keyword arguments to the :class:`~nbgrader.api.Course` object

        Returns
        -------
        course : :class:`~nbgrader.api.Course`

        """
        course = None
        
        try:
            course = self.db.query(Course)\
                .filter(Course.id==course_id)\
                .one()
        except NoResultFound:
            if course_id:
                new_course = Course(id=course_id, **kwargs)
                course = self.db.add(new_course)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return course

    #### Students

    @property
    def students(self):
        """A list of all students in the database."""
        return self.db.query(Student)\
            .order_by(Student.last_name, Student.first_name)\
            .all()

    def add_student(self, student_id, **kwargs):
        """Add a new student to the database.

        Parameters
        ----------
        student_id : string
            The unique id of the student
        `**kwargs` : dict
            other keyword arguments to the :class:`~nbgrader.api.Student` object

        Returns
        -------
        student : :class:`~nbgrader.api.Student`

        """
        if self.authenticator:
            self.authenticator.add_student_to_course(student_id, self.course_id)

        student = Student(id=student_id, **kwargs)
        self.db.add(student)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

        return student

    def find_student(self, student_id):
        """Find a student.

        Parameters
        ----------
        student_id : string
            The unique id of the student

        Returns
        -------
        student : :class:`~nbgrader.api.Student`

        """

        try:
            student = self.db.query(Student)\
                .filter(Student.id == student_id)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such student: {}".format(student_id))

        return student

    def update_or_create_student(self, student_id, **kwargs):
        """Update an existing student, or create it if it doesn't exist.

        Parameters
        ----------
        student_id : string
            The unique id of the student
        `**kwargs`
            additional keyword arguments for the :class:`~nbgrader.api.Student` object

        Returns
        -------
        student : :class:`~nbgrader.api.Student`

        """

        try:
            student = self.find_student(student_id)
        except MissingEntry:
            student = self.add_student(student_id, **kwargs)
        else:
            # Make sure the student is in the course, even if it's somehow
            # already in the database.
            if self.authenticator:
                self.authenticator.add_student_to_course(
                    student_id, self.course_id)

            for attr in kwargs:
                setattr(student, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                self.db.rollback()
                raise InvalidEntry(*e.args)

        return student

    def remove_student(self, student_id):
        """Deletes an existing student from the gradebook, including any
        submissions the might be associated with that student.

        Parameters
        ----------
        student_id : string
            The unique id of the student

        """
        if self.authenticator:
            self.authenticator.remove_student_from_course(
                student_id, self.course_id)

        student = self.find_student(student_id)

        for submission in student.submissions:
            self.remove_submission(submission.assignment.name, student_id)

        self.db.delete(student)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    # Assignments

    @property
    def assignments(self):
        """A list of all assignments in the gradebook."""
        return self.db.query(Assignment)\
            .order_by(Assignment.duedate, Assignment.name)\
            .all()

    def add_assignment(self, name, **kwargs):
        """Add a new assignment to the gradebook.

        Parameters
        ----------
        name : string
            the unique name of the new assignment
        `**kwargs`
            additional keyword arguments for the :class:`~nbgrader.api.Assignment` object

        Returns
        -------
        assignment : :class:`~nbgrader.api.Assignment`

        """
        if 'duedate' in kwargs:
            kwargs['duedate'] = utils.parse_utc(kwargs['duedate'])
        if 'course_id' not in kwargs:
            kwargs['course_id'] = self.course_id
        assignment = Assignment(name=name, **kwargs)
        self.db.add(assignment)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return assignment

    def find_assignment(self, name):
        """Find an assignment in the gradebook.

        Parameters
        ----------
        name : string
            the unique name of the assignment

        Returns
        -------
        assignment : :class:`~nbgrader.api.Assignment`

        """

        try:
            assignment = self.db.query(Assignment)\
                .filter(Assignment.name == name)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such assignment: {}".format(name))

        return assignment

    def update_or_create_assignment(self, name, **kwargs):
        """Update an existing assignment, or create it if it doesn't exist.

        Parameters
        ----------
        name : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for the :class:`~nbgrader.api.Assignment` object

        Returns
        -------
        assignment : :class:`~nbgrader.api.Assignment`

        """

        try:
            assignment = self.find_assignment(name)
        except MissingEntry:
            assignment = self.add_assignment(name, **kwargs)
        else:
            for attr in kwargs:
                if attr == 'duedate':
                    setattr(assignment, attr, utils.parse_utc(kwargs[attr]))
                else:
                    setattr(assignment, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                self.db.rollback()
                raise InvalidEntry(*e.args)

        return assignment

    def remove_assignment(self, name):
        """Deletes an existing assignment from the gradebook, including any
        submissions the might be associated with that assignment.

        Parameters
        ----------
        name : string
            the name of the assignment to delete

        """
        assignment = self.find_assignment(name)

        for submission in assignment.submissions:
            self.remove_submission(name, submission.student.id)

        for notebook in assignment.notebooks:
            self.remove_notebook(notebook.name, name)

        self.db.delete(assignment)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    # Notebooks

    def add_notebook(self, name, assignment, **kwargs):
        """Add a new notebook to an assignment.

        Parameters
        ----------
        name : string
            the name of the new notebook
        assignment : string
            the name of an existing assignment
        `**kwargs`
            additional keyword arguments for the :class:`~nbgrader.api.Notebook` object

        Returns
        -------
        notebook : :class:`~nbgrader.api.Notebook`

        """

        notebook = Notebook(
            name=name, assignment=self.find_assignment(assignment), **kwargs)
        self.db.add(notebook)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return notebook

    def find_notebook(self, name, assignment):
        """Find a particular notebook in an assignment.

        Parameters
        ----------
        name : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        notebook : :class:`~nbgrader.api.Notebook`

        """

        try:
            notebook = self.db.query(Notebook)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(Notebook.name == name, Assignment.name == assignment)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such notebook: {}/{}".format(assignment, name))

        return notebook

    def update_or_create_notebook(self, name, assignment, **kwargs):
        """Update an existing notebook, or create it if it doesn't exist.

        Parameters
        ----------
        name : string
            the name of the notebook
        assignment : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for the :class:`~nbgrader.api.Notebook` object

        Returns
        -------
        notebook : :class:`~nbgrader.api.Notebook`

        """

        try:
            notebook = self.find_notebook(name, assignment)
        except MissingEntry:
            notebook = self.add_notebook(name, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(notebook, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                self.db.rollback()
                raise InvalidEntry(*e.args)

        return notebook

    def remove_notebook(self, name, assignment):
        """Deletes an existing notebook from the gradebook, including any
        submissions the might be associated with that notebook.

        Parameters
        ----------
        name : string
            the name of the notebook to delete
        assignment : string
            the name of an existing assignment

        """
        notebook = self.find_notebook(name, assignment)

        for submission in notebook.submissions:
            self.remove_submission_notebook(name, assignment, submission.student.id)

        for grade_cell in notebook.grade_cells:
            self.db.delete(grade_cell)
        for solution_cell in notebook.solution_cells:
            self.db.delete(solution_cell)
        for source_cell in notebook.source_cells:
            self.db.delete(source_cell)
        for task_cell in notebook.task_cells:
            self.db.delete(task_cell)
        self.db.delete(notebook)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    # Grade cells

    def add_grade_cell(self, name, notebook, assignment, **kwargs):
        """Add a new grade cell to an existing notebook of an existing
        assignment.

        Parameters
        ----------
        name : string
            the name of the new grade cell
        notebook : string
            the name of an existing notebook
        assignment : string
            the name of an existing assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.GradeCell`

        Returns
        -------
        grade_cell : :class:`~nbgrader.api.GradeCell`

        """

        notebook = self.find_notebook(notebook, assignment)
        grade_cell = GradeCell(name=name, notebook=notebook, **kwargs)
        self.db.add(grade_cell)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return grade_cell

    def find_grade_cell(self, name, notebook, assignment):
        """Find a grade cell in a particular notebook of an assignment.

        Parameters
        ----------
        name : string
            the name of the grade cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        grade_cell : :class:`~nbgrader.api.GradeCell`

        """

        try:
            grade_cell = self.db.query(GradeCell)\
                .join(Notebook, Notebook.id == GradeCell.notebook_id)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(
                    GradeCell.name == name,
                    Notebook.name == notebook,
                    Assignment.name == assignment)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such grade cell: {}/{}/{}".format(assignment, notebook, name))

        return grade_cell

    def find_graded_cell(self, name, notebook, assignment):
        """Find a graded cell in a particular notebook of an assignment. This can be either a GradeCell or a TaskCell

        Parameters
        ----------
        name : string
            the name of the grade cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        grade_cell : :class:`~nbgrader.api.GradeCell` or :class:`~nbgrader.api.TaskCell`

        """

        try:
            grade_cell = self.db.query(GradeCell)\
                .join(Notebook, Notebook.id == GradeCell.notebook_id)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(
                    GradeCell.name == name,
                    Notebook.name == notebook,
                    Assignment.name == assignment)\
                .one()
        except NoResultFound:
            try:
                grade_cell = self.db.query(TaskCell)\
                    .join(Notebook, Notebook.id == TaskCell.notebook_id)\
                    .join(Assignment, Assignment.id == Notebook.assignment_id)\
                    .filter(
                        TaskCell.name == name,
                        Notebook.name == notebook,
                        Assignment.name == assignment)\
                    .one()
            except NoResultFound:
                raise MissingEntry("No such grade cell: {}/{}/{}".format(assignment, notebook, name))

        return grade_cell

    def update_or_create_grade_cell(self, name, notebook, assignment, **kwargs):
        """Update an existing grade cell in a notebook of an assignment, or
        create the grade cell if it does not exist.

        Parameters
        ----------
        name : string
            the name of the grade cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.GradeCell`

        Returns
        -------
        grade_cell : :class:`~nbgrader.api.GradeCell`

        """

        try:
            grade_cell = self.find_grade_cell(name, notebook, assignment)
        except MissingEntry:
            grade_cell = self.add_grade_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(grade_cell, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                self.db.rollback()
                raise InvalidEntry(*e.args)

        return grade_cell

    # Solution cells

    def add_solution_cell(self, name, notebook, assignment, **kwargs):
        """Add a new solution cell to an existing notebook of an existing
        assignment.

        Parameters
        ----------
        name : string
            the name of the new solution cell
        notebook : string
            the name of an existing notebook
        assignment : string
            the name of an existing assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SolutionCell`

        Returns
        -------
        solution_cell : :class:`~nbgrader.api.SolutionCell`

        """

        notebook = self.find_notebook(notebook, assignment)
        solution_cell = SolutionCell(name=name, notebook=notebook, **kwargs)
        self.db.add(solution_cell)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return solution_cell

    def find_solution_cell(self, name, notebook, assignment):
        """Find a solution cell in a particular notebook of an assignment.

        Parameters
        ----------
        name : string
            the name of the solution cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        solution_cell : :class:`~nbgrader.api.SolutionCell`

        """

        try:
            solution_cell = self.db.query(SolutionCell)\
                .join(Notebook, Notebook.id == SolutionCell.notebook_id)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(SolutionCell.name == name, Notebook.name == notebook, Assignment.name == assignment)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such solution cell: {}/{}/{}".format(assignment, notebook, name))

        return solution_cell

    def update_or_create_solution_cell(self, name, notebook, assignment, **kwargs):
        """Update an existing solution cell in a notebook of an assignment, or
        create the solution cell if it does not exist.

        Parameters
        ----------
        name : string
            the name of the solution cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SolutionCell`

        Returns
        -------
        solution_cell : :class:`~nbgrader.api.SolutionCell`

        """

        try:
            solution_cell = self.find_solution_cell(name, notebook, assignment)
        except MissingEntry:
            solution_cell = self.add_solution_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(solution_cell, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                raise InvalidEntry(*e.args)

        return solution_cell

# Task cells

    def add_task_cell(self, name, notebook, assignment, **kwargs):
        """Add a new task cell to an existing notebook of an existing
        assignment.

        Parameters
        ----------
        name : string
            the name of the new solution cell
        notebook : string
            the name of an existing notebook
        assignment : string
            the name of an existing assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.TaskCell`

        Returns
        -------
        solution_cell : :class:`~nbgrader.api.TaskCell`

        """

        notebook = self.find_notebook(notebook, assignment)
        task_cell = TaskCell(name=name, notebook=notebook, **kwargs)
        self.db.add(task_cell)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return task_cell

    def find_task_cell(self, name, notebook, assignment):
        """Find a task cell in a particular notebook of an assignment.

        Parameters
        ----------
        name : string
            the name of the solution cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        solution_cell : :class:`~nbgrader.api.TaskCell`

        """

        try:
            task_cell = self.db.query(TaskCell)\
                .join(Notebook, Notebook.id == TaskCell.notebook_id)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(TaskCell.name == name, Notebook.name == notebook, Assignment.name == assignment)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such task cell: {}/{}/{}".format(assignment, notebook, name))

        return task_cell

    def update_or_create_task_cell(self, name, notebook, assignment, **kwargs):
        """Update an existing task cell in a notebook of an assignment, or
        create the solution cell if it does not exist.

        Parameters
        ----------
        name : string
            the name of the solution cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.TaskCell`

        Returns
        -------
        task_cell : :class:`~nbgrader.api.TaskCell`

        """

        try:
            task_cell = self.find_task_cell(name, notebook, assignment)
        except MissingEntry:
            task_cell = self.add_task_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(task_cell, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                raise InvalidEntry(*e.args)

        return task_cell

    # Source cells

    def add_source_cell(self, name, notebook, assignment, **kwargs):
        """Add a new source cell to an existing notebook of an existing
        assignment.

        Parameters
        ----------
        name : string
            the name of the new source cell
        notebook : string
            the name of an existing notebook
        assignment : string
            the name of an existing assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SourceCell`

        Returns
        -------
        source_cell : :class:`~nbgrader.api.SourceCell`

        """

        notebook = self.find_notebook(notebook, assignment)
        source_cell = SourceCell(name=name, notebook=notebook, **kwargs)
        self.db.add(source_cell)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)
        return source_cell

    def find_source_cell(self, name, notebook, assignment):
        """Find a source cell in a particular notebook of an assignment.

        Parameters
        ----------
        name : string
            the name of the source cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment

        Returns
        -------
        source_cell : :class:`~nbgrader.api.SourceCell`

        """

        try:
            source_cell = self.db.query(SourceCell)\
                .join(Notebook, Notebook.id == SourceCell.notebook_id)\
                .join(Assignment, Assignment.id == Notebook.assignment_id)\
                .filter(SourceCell.name == name, Notebook.name == notebook, Assignment.name == assignment)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such source cell: {}/{}/{}".format(assignment, notebook, name))

        return source_cell

    def update_or_create_source_cell(self, name, notebook, assignment, **kwargs):
        """Update an existing source cell in a notebook of an assignment, or
        create the source cell if it does not exist.

        Parameters
        ----------
        name : string
            the name of the source cell
        notebook : string
            the name of the notebook
        assignment : string
            the name of the assignment
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SourceCell`

        Returns
        -------
        source_cell : :class:`~nbgrader.api.SourceCell`

        """

        try:
            source_cell = self.find_source_cell(name, notebook, assignment)
        except MissingEntry:
            source_cell = self.add_source_cell(name, notebook, assignment, **kwargs)
        else:
            for attr in kwargs:
                setattr(source_cell, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                raise InvalidEntry(*e.args)

        return source_cell

    # Submissions

    def add_submission(self, assignment, student, **kwargs):
        """Add a new submission of an assignment by a student.

        This method not only creates the high-level submission object, but also
        mirrors the entire structure of the existing assignment. Thus, once this
        method has been called, the new submission exists and is completely
        ready to be filled in with grades and comments.

        Parameters
        ----------
        assignment : string
            the name of an existing assignment
        student : string
            the name of an existing student
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SubmittedAssignment`

        Returns
        -------
        submission : :class:`~nbgrader.api.SubmittedAssignment`

        """

        if 'timestamp' in kwargs:
            kwargs['timestamp'] = utils.parse_utc(kwargs['timestamp'])

        try:
            submission = SubmittedAssignment(
                assignment=self.find_assignment(assignment),
                student=self.find_student(student),
                **kwargs)

            for notebook in submission.assignment.notebooks:
                nb = SubmittedNotebook(notebook=notebook, assignment=submission)

                for grade_cell in notebook.grade_cells:
                    Grade(cell_id=grade_cell.id, notebook=nb)

                for solution_cell in notebook.solution_cells:
                    Comment(cell_id=solution_cell.id, notebook=nb)

                for task_cell in notebook.task_cells:
                    Comment(cell_id=task_cell.id, notebook=nb)
                    Grade(cell_id=task_cell.id, notebook=nb)

            self.db.add(submission)
            self.db.commit()

        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

        return submission

    def find_submission(self, assignment, student):
        """Find a student's submission for a given assignment.

        Parameters
        ----------
        assignment : string
            the name of an assignment
        student : string
            the unique id of a student

        Returns
        -------
        submission : :class:`~nbgrader.api.SubmittedAssignment`

        """

        try:
            submission = self.db.query(SubmittedAssignment)\
                .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                .join(Student, Student.id == SubmittedAssignment.student_id)\
                .filter(Assignment.name == assignment, Student.id == student)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such submission: {} for {}".format(
                assignment, student))

        return submission

    def update_or_create_submission(self, assignment, student, **kwargs):
        """Update an existing submission of an assignment by a given student,
        or create a new submission if it doesn't exist.

        See :func:`~nbgrader.api.Gradebook.add_submission` for additional
        details.

        Parameters
        ----------
        assignment : string
            the name of an existing assignment
        student : string
            the name of an existing student
        `**kwargs`
            additional keyword arguments for :class:`~nbgrader.api.SubmittedAssignment`

        Returns
        -------
        submission : :class:`~nbgrader.api.SubmittedAssignment`

        """

        try:
            submission = self.find_submission(assignment, student)
        except MissingEntry:
            submission = self.add_submission(assignment, student, **kwargs)
        else:
            for attr in kwargs:
                if attr == 'timestamp':
                    setattr(submission, attr, utils.parse_utc(kwargs[attr]))
                else:
                    setattr(submission, attr, kwargs[attr])
            try:
                self.db.commit()
            except (IntegrityError, FlushError) as e:
                self.db.rollback()
                raise InvalidEntry(*e.args)

        return submission

    def grant_extension(self, assignment, student, minutes=0, hours=0, days=0, weeks=0):
        """Gives an extension to a student for an assignment.

        Note that extensions do not stack: if you call this method multiple
        times for the same assignment and student, the extension will be
        replaced. So if you want to extend an assignment by two days, and then
        another day, you will need to call this method with days=3 the second
        time.

        If you do not provide any of the time arguments (minutes, hours, days,
        weeks), then any existing extension will be removed.

        Parameters
        ----------
        assignment : string
            the name of an assignment
        student : string
            the unique id of a student
        minutes : number (default=0)
            The number of minutes in the extension
        hours : number (default=0)
            The number of hours in the extension
        days : number (default=0)
            The number of days in the extension
        weeks : number (default=0)
            The number of weeks in the extension

        """
        submission = self.find_submission(assignment, student)
        if minutes == 0 and hours == 0 and days == 0 and weeks == 0:
            submission.extension = None
        else:
            submission.extension = datetime.timedelta(
                minutes=minutes, hours=hours, days=days, weeks=weeks)
        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    def remove_submission(self, assignment, student):
        """Removes a submission from the database.

        Parameters
        ----------
        assignment : string
            the name of an assignment
        student : string
            the name of a student

        """
        submission = self.find_submission(assignment, student)

        for notebook in submission.notebooks:
            self.remove_submission_notebook(notebook.name, assignment, student)

        self.db.delete(submission)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    def remove_submission_notebook(self, notebook, assignment, student):
        """Removes a submitted notebook from the database.

        Parameters
        ----------
        notebook : string
            the name of a notebook
        assignment : string
            the name of an assignment
        student : string
            the name of a student

        """
        submission = self.find_submission_notebook(notebook, assignment, student)

        for grade in submission.grades:
            self.db.delete(grade)
        for comment in submission.comments:
            self.db.delete(comment)
        self.db.delete(submission)

        try:
            self.db.commit()
        except (IntegrityError, FlushError) as e:
            self.db.rollback()
            raise InvalidEntry(*e.args)

    def assignment_submissions(self, assignment):
        """Find all submissions of a given assignment.

        Parameters
        ----------
        assignment : string
            the name of an assignment

        Returns
        -------
        submissions : list
            A list of :class:`~nbgrader.api.SubmittedAssignment` objects

        """

        return self.db.query(SubmittedAssignment)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .filter(Assignment.name == assignment)\
            .all()

    def notebook_submissions(self, notebook, assignment):
        """Find all submissions of a given notebook in a given assignment.

        Parameters
        ----------
        notebook : string
            the name of a notebook
        assignment : string
            the name of an assignment

        Returns
        -------
        submissions : list
            A list of :class:`~nbgrader.api.SubmittedNotebook` objects

        """

        return self.db.query(SubmittedNotebook)\
            .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
            .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
            .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
            .filter(Notebook.name == notebook, Assignment.name == assignment)\
            .all()

    def student_submissions(self, student):
        """Find all submissions by a given student.

        Parameters
        ----------
        student : string
            the student's unique id

        Returns
        -------
        submissions : list
            A list of :class:`~nbgrader.api.SubmittedAssignment` objects

        """

        return self.db.query(SubmittedAssignment)\
            .join(Student, Student.id == SubmittedAssignment.student_id)\
            .filter(Student.id == student)\
            .all()

    def find_submission_notebook(self, notebook, assignment, student):
        """Find a particular notebook in a student's submission for a given
        assignment.

        Parameters
        ----------
        notebook : string
            the name of a notebook
        assignment : string
            the name of an assignment
        student : string
            the unique id of a student

        Returns
        -------
        notebook : :class:`~nbgrader.api.SubmittedNotebook`

        """

        try:
            notebook = self.db.query(SubmittedNotebook)\
                .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
                .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
                .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                .join(Student, Student.id == SubmittedAssignment.student_id)\
                .filter(
                    Notebook.name == notebook,
                    Assignment.name == assignment,
                    Student.id == student)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such submitted notebook: {}/{} for {}".format(
                assignment, notebook, student))

        return notebook

    def find_submission_notebook_by_id(self, notebook_id):
        """Find a submitted notebook by its unique id.

        Parameters
        ----------
        notebook_id : string
            the unique id of the submitted notebook

        Returns
        -------
        notebook : :class:`~nbgrader.api.SubmittedNotebook`

        """

        try:
            notebook = self.db.query(SubmittedNotebook)\
                .filter(SubmittedNotebook.id == notebook_id)\
                .one()
        except NoResultFound:
            raise MissingEntry("No such submitted notebook: {}".format(notebook_id))

        return notebook

    def find_grade(self, grade_cell, notebook, assignment, student):
        """Find a particular grade in a notebook in a student's submission
        for a given assignment.

        Parameters
        ----------
        grade_cell : string
            the name of a grade or task cell
        notebook : string
            the name of a notebook
        assignment : string
            the name of an assignment
        student : string
            the unique id of a student

        Returns
        -------
        grade : :class:`~nbgrader.api.Grade`

        """
        try:
            grade = self.db.query(Grade)\
                .join(GradeCell, GradeCell.id == Grade.cell_id)\
                .join(SubmittedNotebook, SubmittedNotebook.id == Grade.notebook_id)\
                .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
                .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
                .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                .join(Student, Student.id == SubmittedAssignment.student_id)\
                .filter(
                    GradeCell.name == grade_cell,
                    Notebook.name == notebook,
                    Assignment.name == assignment,
                    Student.id == student)\
                .one()
        except NoResultFound:
            try:
                grade = self.db.query(Grade)\
                    .join(TaskCell, TaskCell.id == Grade.cell_id)\
                    .join(SubmittedNotebook, SubmittedNotebook.id == Grade.notebook_id)\
                    .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
                    .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
                    .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                    .join(Student, Student.id == SubmittedAssignment.student_id)\
                    .filter(
                        TaskCell.name == grade_cell,
                        Notebook.name == notebook,
                        Assignment.name == assignment,
                        Student.id == student)\
                    .one()
            except NoResultFound:
                raise MissingEntry("No such grade: {}/{}/{} for {}".format(
                    assignment, notebook, grade_cell, student))

        return grade

    def find_grade_by_id(self, grade_id):
        """Find a grade by its unique id.

        Parameters
        ----------
        grade_id : string
            the unique id of the grade

        Returns
        -------
        grade : :class:`~nbgrader.api.Grade`

        """

        try:
            grade = self.db.query(Grade).filter(Grade.id == grade_id).one()
        except NoResultFound:
            raise MissingEntry("No such grade: {}".format(grade_id))

        return grade

    def find_comment(self, solution_cell, notebook, assignment, student):
        """Find a particular comment in a notebook in a student's submission
        for a given assignment.

        Parameters
        ----------
        solution_cell : string
            the name of a solution or task cell
        notebook : string
            the name of a notebook
        assignment : string
            the name of an assignment
        student : string
            the unique id of a student

        Returns
        -------
        comment : :class:`~nbgrader.api.Comment`

        """

        try:
            comment = self.db.query(Comment)\
                .join(SolutionCell, SolutionCell.id == Comment.cell_id)\
                .join(SubmittedNotebook, SubmittedNotebook.id == Comment.notebook_id)\
                .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
                .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
                .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                .join(Student, Student.id == SubmittedAssignment.student_id)\
                .filter(
                    SolutionCell.name == solution_cell,
                    Notebook.name == notebook,
                    Assignment.name == assignment,
                    Student.id == student)\
                .one()
        except NoResultFound:
            try:
                comment = self.db.query(Comment)\
                    .join(TaskCell, TaskCell.id == Comment.cell_id)\
                    .join(SubmittedNotebook, SubmittedNotebook.id == Comment.notebook_id)\
                    .join(Notebook, Notebook.id == SubmittedNotebook.notebook_id)\
                    .join(SubmittedAssignment, SubmittedAssignment.id == SubmittedNotebook.assignment_id)\
                    .join(Assignment, Assignment.id == SubmittedAssignment.assignment_id)\
                    .join(Student, Student.id == SubmittedAssignment.student_id)\
                    .filter(
                        TaskCell.name == solution_cell,
                        Notebook.name == notebook,
                        Assignment.name == assignment,
                        Student.id == student)\
                    .one()
            except NoResultFound:
                raise MissingEntry("No such taskcomment: {}/{}/{} for {}".format(
                    assignment, notebook, solution_cell, student))

        return comment

    def find_comment_by_id(self, comment_id):
        """Find a comment by its unique id.

        Parameters
        ----------
        comment_id : string
            the unique id of the comment

        Returns
        -------
        comment : :class:`~nbgrader.api.Comment`

        """

        try:
            comment = self.db.query(Comment).filter(Comment.id == comment_id).one()
        except NoResultFound:
            raise MissingEntry("No such comment: {}".format(comment_id))

        return comment

    def average_assignment_score(self, assignment_id):
        """Compute the average score for an assignment.

        Parameters
        ----------
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average score

        """

        assignment = self.find_assignment(assignment_id)
        if assignment.num_submissions == 0:
            return 0.0

        score_sum_gradecell = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(GradeCell, Notebook, Assignment)\
            .filter(Assignment.name == assignment_id).scalar()
        score_sum_taskcell = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(TaskCell, Notebook, Assignment)\
            .filter(Assignment.name == assignment_id).scalar()
        score_sum = score_sum_gradecell + score_sum_taskcell
        return score_sum / assignment.num_submissions

    def average_assignment_code_score(self, assignment_id):
        """Compute the average code score for an assignment.

        Parameters
        ----------
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average code score

        """

        assignment = self.find_assignment(assignment_id)
        if assignment.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(GradeCell, Notebook, Assignment)\
            .filter(and_(
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                GradeCell.notebook_id == Notebook.id,
                Grade.cell_id == GradeCell.id,
                GradeCell.cell_type == "code")).scalar()
        return score_sum / assignment.num_submissions

    def average_assignment_written_score(self, assignment_id):
        """Compute the average written score for an assignment.

        Parameters
        ----------
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average written score

        """

        assignment = self.find_assignment(assignment_id)
        if assignment.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(GradeCell, Notebook, Assignment)\
            .filter(and_(
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                GradeCell.notebook_id == Notebook.id,
                Grade.cell_id == GradeCell.id,
                GradeCell.cell_type == "markdown")).scalar()
        return score_sum / assignment.num_submissions

    def average_assignment_task_score(self, assignment_id):
        """Compute the average task score for an assignment.

        Parameters
        ----------
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average task score

        """

        assignment = self.find_assignment(assignment_id)
        if assignment.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(TaskCell, Notebook, Assignment)\
            .filter(and_(
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                TaskCell.notebook_id == Notebook.id,
                Grade.cell_id == TaskCell.id,
                TaskCell.cell_type == "markdown")).scalar()
        return score_sum / assignment.num_submissions

    def average_notebook_score(self, notebook_id, assignment_id):
        """Compute the average score for a particular notebook in an assignment.

        Parameters
        ----------
        notebook_id : string
            the name of the notebook
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average notebook score

        """

        notebook = self.find_notebook(notebook_id, assignment_id)
        if notebook.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(SubmittedNotebook, Notebook, Assignment)\
            .filter(and_(
                Notebook.name == notebook_id,
                Assignment.name == assignment_id)).scalar()
        return score_sum / notebook.num_submissions

    def average_notebook_code_score(self, notebook_id, assignment_id):
        """Compute the average code score for a particular notebook in an
        assignment.

        Parameters
        ----------
        notebook_id : string
            the name of the notebook
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average notebook code score

        """

        notebook = self.find_notebook(notebook_id, assignment_id)
        if notebook.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(GradeCell, Notebook, Assignment)\
            .filter(and_(
                Notebook.name == notebook_id,
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                GradeCell.notebook_id == Notebook.id,
                Grade.cell_id == GradeCell.id,
                GradeCell.cell_type == "code")).scalar()
        return score_sum / notebook.num_submissions

    def average_notebook_written_score(self, notebook_id, assignment_id):
        """Compute the average written score for a particular notebook in an
        assignment.

        Parameters
        ----------
        notebook_id : string
            the name of the notebook
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average notebook written score

        """

        notebook = self.find_notebook(notebook_id, assignment_id)
        if notebook.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(GradeCell, Notebook, Assignment)\
            .filter(and_(
                Notebook.name == notebook_id,
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                GradeCell.notebook_id == Notebook.id,
                Grade.cell_id == GradeCell.id,
                GradeCell.cell_type == "markdown")).scalar()
        return score_sum / notebook.num_submissions

    def average_notebook_task_score(self, notebook_id, assignment_id):
        """Compute the average task score for a particular notebook in an
        assignment.

        Parameters
        ----------
        notebook_id : string
            the name of the notebook
        assignment_id : string
            the name of the assignment

        Returns
        -------
        score : float
            The average notebook task score

        """

        notebook = self.find_notebook(notebook_id, assignment_id)
        if notebook.num_submissions == 0:
            return 0.0

        score_sum = self.db.query(func.coalesce(func.sum(Grade.score), 0.0))\
            .join(TaskCell, Notebook, Assignment)\
            .filter(and_(
                Notebook.name == notebook_id,
                Assignment.name == assignment_id,
                Notebook.assignment_id == Assignment.id,
                TaskCell.notebook_id == Notebook.id,
                Grade.cell_id == TaskCell.id,
                TaskCell.cell_type == "markdown")).scalar()
        return score_sum / notebook.num_submissions

    def student_dicts(self):
        """Returns a list of dictionaries containing student data. Equivalent
        to calling :func:`~nbgrader.api.Student.to_dict` for each student,
        except that this method is implemented using proper SQL joins and is
        much faster.

        Returns
        -------
        students : list
            A list of dictionaries, one per student

        """
        max_scores = self.db.query(
            Assignment.id,
            func.sum(Assignment.max_score).label("max_score")
        ).group_by(Assignment.id).subquery()
        _max_scores = func.coalesce(max_scores.c.max_score, 0.0)
        total_score, = self.db.query(func.sum(_max_scores)).one()

        if len(self.assignments) > 0 and total_score > 0:
            # subquery the scores
            scores = self.db.query(
                Student.id,
                func.sum(Grade.score).label("score")
            ).join(SubmittedAssignment, SubmittedNotebook, Grade)\
             .group_by(Student.id)\
             .subquery()

            # full query
            _scores = func.coalesce(scores.c.score, 0.0)
            students = self.db.query(
                Student.id, Student.first_name, Student.last_name,
                Student.email, _scores,
                func.sum(Assignment.max_score), Student.lms_user_id
            ).outerjoin(scores, Student.id == scores.c.id)\
             .group_by(
                 Student.id, Student.first_name, Student.last_name,
                 Student.email, _scores, Student.lms_user_id)\
             .all()

            keys = ["id", "first_name", "last_name", "email", "score", "max_score", "lms_user_id"]
            return [dict(zip(keys, x)) for x in students]

        else:
            students = [s.to_dict() for s in self.students]
            return students

    def submission_dicts(self, assignment_id):
        """Returns a list of dictionaries containing submission data. Equivalent
        to calling :func:`~nbgrader.api.SubmittedAssignment.to_dict` for each
        submission, except that this method is implemented using proper SQL
        joins and is much faster.

        Parameters
        ----------
        assignment_id : string
            the name of the assignment

        Returns
        -------
        submissions : list
            A list of dictionaries, one per submitted assignment

        """
        # subquery the code scores
        code_scores = self.db.query(
            SubmittedAssignment.id.label("id"),
            func.sum(Grade.score).label("code_score"),
            func.sum(GradeCell.max_score).label("max_code_score"),
        ).select_from(SubmittedAssignment
        ).join(SubmittedNotebook, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "code")\
         .group_by(SubmittedAssignment.id)\
         .subquery()

        # subquery for the written scores
        written_scores = self.db.query(
            SubmittedAssignment.id.label("id"),
            func.sum(Grade.score).label("written_score"),
            func.sum(GradeCell.max_score).label("max_written_score"),
        ).select_from(SubmittedAssignment
        ).join(SubmittedNotebook, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "markdown")\
         .group_by(SubmittedAssignment.id)\
         .subquery()

        # subquery for the task scores
        task_scores = self.db.query(
            SubmittedAssignment.id.label("id"),
            func.sum(Grade.score).label("task_score"),
            func.sum(TaskCell.max_score).label("max_task_score"),
        ).select_from(SubmittedAssignment
        ).join(SubmittedNotebook, Notebook, Assignment, Student, Grade, TaskCell)\
         .filter(TaskCell.cell_type == "markdown")\
         .group_by(SubmittedAssignment.id)\
         .subquery()

        # subquery for needing manual grading
        manual_grade = self.db.query(
            SubmittedAssignment.id,
            exists().where(Grade.needs_manual_grade).label("needs_manual_grade")
        ).select_from(SubmittedAssignment
        ).join(SubmittedNotebook, Assignment, Notebook)\
         .filter(
             SubmittedNotebook.assignment_id == SubmittedAssignment.id,
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.needs_manual_grade)\
         .group_by(SubmittedAssignment.id)\
         .subquery()

        all_scores = aliased(union_all(
            self.db.query(
                SubmittedAssignment.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(GradeCell.max_score).label("max_score"),
            ).select_from(SubmittedAssignment
            ).join(SubmittedNotebook, Grade, GradeCell)
            .filter(GradeCell.cell_type == "code")
            .group_by(SubmittedAssignment.id),
            # subquery for the written scores
            self.db.query(
                SubmittedAssignment.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(GradeCell.max_score).label("max_score"),
            ).select_from(SubmittedAssignment
            ).join(SubmittedNotebook, Grade, GradeCell)\
            .filter(GradeCell.cell_type == "markdown")\
            .group_by(SubmittedAssignment.id),

            self.db.query(
                SubmittedAssignment.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(TaskCell.max_score).label("max_score"),
            ).select_from(SubmittedAssignment
            ).join(SubmittedNotebook, Grade, TaskCell)\
            .filter(TaskCell.cell_type == "markdown")\
            .group_by(SubmittedAssignment.id)
        )
        )
        total_scores = self.db.query(
            func.sum(all_scores.c.score).label("score"),
            func.sum(all_scores.c.max_score).label("max_score"),
            all_scores.c.id.label("id"),
        ).group_by(all_scores.c.id)\
         .subquery()

        # full query
        _manual_grade = func.coalesce(manual_grade.c.needs_manual_grade, False)
        assignments = self.db.query(
            SubmittedAssignment.id, Assignment.name,
            SubmittedAssignment.timestamp, Student.first_name, Student.last_name,
            Student.id,
            func.coalesce(total_scores.c.score, 0.0),
            func.coalesce(total_scores.c.max_score, 0.0),
            func.coalesce(code_scores.c.code_score, 0.0),
            func.coalesce(code_scores.c.max_code_score, 0.0),
            func.coalesce(written_scores.c.written_score, 0.0),
            func.coalesce(written_scores.c.max_written_score, 0.0),
            func.coalesce(task_scores.c.task_score, 0.0),
            func.coalesce(task_scores.c.max_task_score, 0.0),
            _manual_grade
        ).select_from(SubmittedAssignment
        ).join(SubmittedNotebook, Assignment, Student, Grade)\
         .outerjoin(code_scores, SubmittedAssignment.id == code_scores.c.id)\
         .outerjoin(written_scores, SubmittedAssignment.id == written_scores.c.id)\
         .outerjoin(task_scores, SubmittedAssignment.id == task_scores.c.id)\
         .outerjoin(manual_grade, SubmittedAssignment.id == manual_grade.c.id)\
         .outerjoin(total_scores, SubmittedAssignment.id == total_scores.c.id)\
         .filter(and_(
             Assignment.name == assignment_id,
             Student.id == SubmittedAssignment.student_id,
             SubmittedAssignment.id == SubmittedNotebook.assignment_id,
             SubmittedNotebook.id == Grade.notebook_id,
             SubmittedAssignment.id == total_scores.c.id))\
         .group_by(
             SubmittedAssignment.id, Assignment.name,
             SubmittedAssignment.timestamp, Student.first_name, Student.last_name,
             Student.id, code_scores.c.code_score, code_scores.c.max_code_score,
             written_scores.c.written_score, written_scores.c.max_written_score,
             task_scores.c.task_score, task_scores.c.max_task_score,
             total_scores.c.score, total_scores.c.max_score,
             _manual_grade)\
         .all()

        keys = [
            "id", "name", "timestamp", "first_name", "last_name", "student",
            "score", "max_score", "code_score", "max_code_score",
            "written_score", "max_written_score",
            "task_score", "max_task_score",
            "needs_manual_grade"
        ]
        return [dict(zip(keys, x)) for x in assignments]

    def notebook_submission_dicts(self, notebook_id, assignment_id):
        """Returns a list of dictionaries containing submission data. Equivalent
        to calling :func:`~nbgrader.api.SubmittedNotebook.to_dict` for each
        submission, except that this method is implemented using proper SQL
        joins and is much faster.

        Parameters
        ----------
        notebook_id : string
            the name of the notebook
        assignment_id : string
            the name of the assignment

        Returns
        -------
        submissions : list
            A list of dictionaries, one per submitted notebook

        """
        # subquery the code scores
        code_scores = self.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("code_score"),
            func.sum(GradeCell.max_score).label("max_code_score"),
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "code")\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # subquery for the written scores
        written_scores = self.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("written_score"),
            func.sum(GradeCell.max_score).label("max_written_score"),
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "markdown")\
         .group_by(SubmittedNotebook.id)\
         .subquery()
        # subquery for the written scores
        task_scores = self.db.query(
            SubmittedNotebook.id,
            func.coalesce(func.sum(Grade.score), 0.0).label("task_score"),
            func.sum(TaskCell.max_score).label("max_task_score"),
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, TaskCell)\
         .filter(TaskCell.cell_type == "markdown")\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        max_scores = self.db.query(
            SubmittedNotebook.id,
            func.sum(task_scores.c.max_task_score).label("mmmm"),
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, task_scores)\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        all_scores = aliased(union_all(
            self.db.query(
                SubmittedNotebook.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(GradeCell.max_score).label("max_score"),
            ).select_from(SubmittedNotebook
            ).join(Grade, GradeCell)
            .filter(GradeCell.cell_type == "code")
            .group_by(SubmittedNotebook.id),
            # subquery for the written scores
            self.db.query(
                SubmittedNotebook.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(GradeCell.max_score).label("max_score"),
            ).select_from(SubmittedNotebook
            ).join(Grade, GradeCell)\
            .filter(GradeCell.cell_type == "markdown")\
            .group_by(SubmittedNotebook.id),

            self.db.query(
                SubmittedNotebook.id.label('id'),
                func.sum(Grade.score).label("score"),
                func.sum(TaskCell.max_score).label("max_score"),
            ).select_from(SubmittedNotebook
            ).join(Grade, TaskCell)\
            .filter(TaskCell.cell_type == "markdown")\
            .group_by(SubmittedNotebook.id)
        )
        )
        total_scores = self.db.query(
            func.sum(all_scores.c.score).label("score"),
            func.sum(all_scores.c.max_score).label("max_score"),
            all_scores.c.id.label("id"),
        )\
            .group_by(all_scores.c.id)\
            .subquery()

        # subquery for needing manual grading

        manual_grade = self.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.needs_manual_grade).label("needs_manual_grade")
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.needs_manual_grade)\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # subquery for failed tests
        failed_tests = self.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.failed_tests).label("failed_tests")
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.failed_tests)\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # full query
        _manual_grade = func.coalesce(manual_grade.c.needs_manual_grade, False)
        _failed_tests = func.coalesce(failed_tests.c.failed_tests, False)
        submissions = self.db.query(
            SubmittedNotebook.id, Notebook.name,
            Student.id, Student.first_name, Student.last_name,
            func.coalesce(total_scores.c.score, 0.0),
            func.coalesce(total_scores.c.max_score, 0.0),
            func.coalesce(code_scores.c.code_score, 0.0),
            func.coalesce(code_scores.c.max_code_score, 0.0),
            func.coalesce(written_scores.c.written_score, 0.0),
            func.coalesce(written_scores.c.max_written_score, 0.0),
            func.coalesce(task_scores.c.task_score, 0.0),
            func.coalesce(task_scores.c.max_task_score, 0.0),
            _manual_grade, _failed_tests, SubmittedNotebook.flagged
        ).select_from(SubmittedNotebook
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade)\
         .outerjoin(code_scores, SubmittedNotebook.id == code_scores.c.id)\
         .outerjoin(written_scores, SubmittedNotebook.id == written_scores.c.id)\
         .outerjoin(task_scores, SubmittedNotebook.id == task_scores.c.id)\
         .outerjoin(total_scores, SubmittedNotebook.id == total_scores.c.id)\
         .outerjoin(manual_grade, SubmittedNotebook.id == manual_grade.c.id)\
         .outerjoin(failed_tests, SubmittedNotebook.id == failed_tests.c.id)\
         .filter(and_(
             Notebook.name == notebook_id,
             Assignment.name == assignment_id,
             Student.id == SubmittedAssignment.student_id,
             SubmittedAssignment.id == SubmittedNotebook.assignment_id,
             SubmittedNotebook.id == Grade.notebook_id,
             SubmittedNotebook.id == total_scores.c.id,
         )
        ).group_by(
             SubmittedNotebook.id, Notebook.name,
             Student.id, Student.first_name, Student.last_name,
             code_scores.c.code_score, code_scores.c.max_code_score,
             written_scores.c.written_score, written_scores.c.max_written_score,
             task_scores.c.task_score, task_scores.c.max_task_score,
             total_scores.c.score, total_scores.c.max_score,
             _manual_grade, _failed_tests, SubmittedNotebook.flagged)\
         .all()

        keys = [
            "id", "name", "student", "first_name", "last_name",
            "score", "max_score",
            "code_score", "max_code_score",
            "written_score", "max_written_score",
            "task_score", "max_task_score",
            "needs_manual_grade",
            "failed_tests", "flagged"
        ]
        return [dict(zip(keys, x)) for x in submissions]
