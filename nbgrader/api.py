import json
from uuid import uuid4
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class Document(object):

    _defaults = {}

    def __init__(self, **kwargs):
        if '_id' in kwargs:
            self._id = kwargs['_id']
        else:
            self._id = str(uuid4())
        attributes = self._defaults.copy()
        attributes.update(kwargs)
        for field, value in attributes.items():
            if field not in self._defaults and field != '_id':
                raise ValueError("Unexpected attribute: {}".format(field))
            setattr(self, field, value)

    def to_dict(self):
        dict_obj = {'_id': self._id}
        for field in self._defaults:
            value = getattr(self, field)
            if isinstance(value, Document):
                value = value._id
            dict_obj[field] = value
        return dict_obj

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return self.to_json()


class GradeCell(Document):
    _defaults = {
        'grade_id': None,
        'notebook_id': None,
        'assignment': None,
        'max_score': None,
        'source': None,
        'checksum': None
    }


class Grade(Document):
    _defaults = {
        'grade_id': None,
        'max_score': None,
        'autoscore': None,
        'score': None,
        'notebook': None
    }


class Comment(Document):
    _defaults = {
        'comment_id': None,
        'comment': '',
        'notebook': None
    }


class Student(Document):
    _defaults = {
        'student_id': None,
        'first_name': None,
        'last_name': None,
        'email': None
    }


class Notebook(Document):
    _defaults = {
        'notebook_id': None,
        'assignment': None,
        'student': None
    }


class Assignment(Document):
    _defaults = {
        'assignment_id': None,
        'duedate': None
    }


class Gradebook(object):
    _collections = {
        'grade_cells': GradeCell,
        'grades': Grade,
        'comments': Comment,
        'students': Student,
        'notebooks': Notebook,
        'assignments': Assignment
    }

    def __init__(self, name, ip="localhost", port=27017):
        self.client = MongoClient(ip, port)
        self.db = self.client[name]

    def _add(self, collection, document):
        try:
            self.db[collection].insert(document.to_dict())
        except DuplicateKeyError:
            raise DuplicateKeyError("Document already exists in '{}':\n\n{}".format(collection, document))

    def _update(self, collection, document):
        _id = {"_id": document._id}
        doc = document.to_dict()
        del doc['_id']
        self.db[collection].update(_id, {"$set": doc})

    def _find(self, collection, query):
        new_query = {}
        for key, value in query.items():
            if isinstance(value, Document):
                new_query[key] = value._id
            else:
                new_query[key] = value

        document = self.db[collection].find_one(new_query)
        if document:
            document = self._collections[collection](**document)
        return document

    def _find_or_create(self, collection, query):
        document = self._find(collection, query)
        if not document:
            document = self._collections[collection](**query)
            self._add(collection, document)
        return document

    def _find_all(self, collection, query):
        new_query = {}
        for key, value in query.items():
            if isinstance(value, Document):
                new_query[key] = value._id
            else:
                new_query[key] = value

        documents = []
        for document in self.db[collection].find(new_query):
            documents.append(self._collections[collection](**document))
        return documents

    #### Grade cells

    def add_grade_cell(self, grade_cell):
        """Add a new grade cell to the gradebook. If the assignent already
        exists in the gradebook, an error will be thrown.

        Parameters
        ----------
        grade_cell: nbgrader.api.GradeCell
            The new grade cell

        """
        if not isinstance(grade_cell, GradeCell):
            raise ValueError("The new grade cell must be an GradeCell object")
        return self._add('grade_cells', grade_cell)

    def find_or_create_grade_cell(self, **attributes):
        """Look up or create a grade cell by its associated attributes. For
        example:

        >>> gb = Gradebook("example")
        >>> assignment = gb.find_assignment(assignment_id="Problem Set 0")
        >>> gb.find_or_create_grade_cell(grade_id="foo", notebook_id="Problem 1", assignment=assignment)

        will find a grade cell with id "foo" in the notebook "Problem
        1" and with an associated assignment whose id is "Problem Set
        0". If there is more than one matching grade cell, then an
        error will be thrown.

        If there are no matching grade cells, then a new grade cell
        will be created with the given attributes.

        Valid keyword arguments correspond to the attributes for a
        GradeCell.

        """
        return self._find_or_create('grade_cells', attributes)

    def update_grade_cell(self, grade_cell):
        """Update a grade cell.

        Parameters
        ----------
        grade_cell: nbgrader.api.GradeCell
            The grade cell to update.

        """
        self._update('grade_cells', grade_cell)

    #### Assignments

    @property
    def assignments(self):
        """A list of all assignments in the gradebook."""
        return self._find_all('assignments', {})

    def add_assignment(self, assignment):
        """Add a new assignment to the gradebook. If the assignent already
        exists in the gradebook, an error will be thrown.

        Parameters
        ----------
        assignment: nbgrader.api.Assignment
            The new assignment

        """
        if not isinstance(assignment, Assignment):
            raise ValueError("The new assignment must be an Assignment object")
        return self._add('assignments', assignment)

    def find_assignment(self, **attributes):
        """Look up an assignment by its associated attributes. For example:

        >>> gb = Gradebook("example")
        >>> gb.find_assignment(assignment_id="Problem Set 1")

        will find an assignment called "Problem Set 1". If there is
        more than one matching assignment, then an error will be
        thrown.

        Valid keyword arguments correspond to the attributes for an
        Assignment.

        """
        assignment = self._find('assignments', attributes)
        if assignment is None:
            raise ValueError('no such assignment: {}'.format(attributes))
        return assignment

    #### Students

    @property
    def students(self):
        """A list of all students in the gradebook."""
        return self._find_all('students', {})

    def add_student(self, student):
        """Add a new student to the gradebook. If the student already
        exists in the gradebook, an error will be thrown.

        Parameters
        ----------
        student: nbgrader.api.Student
            The new student

        """
        if not isinstance(student, Student):
            raise ValueError("The new student must be a Student object")
        return self._add('students', student)

    def find_student(self, **attributes):
        """Look up student by its associated attributes. For example:

        >>> gb = Gradebook("example")
        >>> gb.find_student(student_id="Hacker")

        will find a student with id "Hacker". If there is more than
        one matching student, then an error will be thrown.

        Valid keyword arguments correspond to the attributes for a
        Student.

        """
        student = self._find('students', attributes)
        if student is None:
            raise ValueError('no such student: {}'.format(attributes))
        return student

    #### Notebooks

    @property
    def notebooks(self):
        """A list of all notebooks in the gradebook."""
        return self._find_all('notebooks', {})

    def add_notebook(self, notebook):
        """Add a new notebook to the gradebook. If the notebook already
        exists in the gradebook, an error will be thrown.

        Parameters
        ----------
        notebook: nbgrader.api.Notebook
            The new notebook

        """
        if not isinstance(notebook, Notebook):
            raise ValueError("The new student must be a Student object")
        return self._add('notebooks', notebook)

    def find_notebook(self, **attributes):
        """Look up notebook by its associated attributes. For example:

        >>> gb = Gradebook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> gb.find_notebook(notebook_id="Problem 1", student=student)

        will find a notebook with id "Problem 1" and with an
        associated students whos id is "Hacker". If there is more than
        one matching notebook, then an error will be thrown.

        Valid keyword arguments correspond to the attributes for a
        Notebook.

        """
        notebook = self._find('notebooks', attributes)
        if notebook is None:
            raise ValueError('no such notebook: {}'.format(attributes))
        return notebook

    def find_or_create_notebook(self, **attributes):
        """Look up or create a notebook by its associated attributes. For
        example:

        >>> gb = Gradebook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> gb.find_or_create_notebook(notebook_id="Problem 1", student=student)

        will find a notebook with id "Problem 1" and with an
        associated student whose id is "Hacker". If there is more than
        one matching notebook, then an error will be thrown.

        If there are no matching notebooks, then a new notebook will
        be created with the given attributes.

        Valid keyword arguments correspond to the attributes for a
        Notebook.

        """
        return self._find_or_create('notebooks', attributes)

    def find_notebooks(self, **attributes):
        """Find all notebooks matching the given attributes. For example:

        >>> gb = Gradebook("example")
        >>> gb.find_notebooks(notebook_id="Problem 1")

        will find all notebooks with id "Problem 1".

        Valid keyword arguments correspond to the attributes for a
        Notebook.

        """
        return self._find_all('notebooks', attributes)

    #### Grades

    def find_or_create_grade(self, **attributes):
        """Look up or create a grade by its associated attributes. For
        example:

        >>> gb = Gradebook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> notebook = gb.find_notebook(notebook_id="Problem 1", student=student)
        >>> gb.find_or_create_grade(grade_id="foo", notebook=notebook)

        will find a grade with id "foo" and with an associated
        notebook whose id is "Problem 1" and whose student has id
        "Hacker". If there is more than one matching grade, then an
        error will be thrown.

        If there are no matching grades, then a new grade will be
        created with the given attributes.

        Valid keyword arguments correspond to the attributes for a
        Grade.

        """
        return self._find_or_create('grades', attributes)

    def find_grade(self, **attributes):
        """Look up a grade by its associated attributes. For example:

        >>> gb = Gradebook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> notebook = gb.find_notebook(notebook_id="Problem 1", student=student)
        >>> gb.find_grade(grade_id="foo", notebook=notebook)

        will find a grade with id "foo" and with an associated
        notebook whose id is "Problem 1" and whose student has id
        "Hacker". If there is more than one matching grade, then an
        error will be thrown.

        Valid keyword arguments correspond to the attributes for a
        Grade.

        """
        grade = self._find('grades', attributes)
        if grade is None:
            raise ValueError('no such grade: {}'.format(attributes))
        return grade

    def find_grades(self, **attributes):
        """Find all grades matching the given attributes. For example:

        >>> gb = Gradebook("example")
        >>> gb.find_grades(grade_id="foo")

        will find all grade with id "foo".

        Valid keyword arguments correspond to the attributes for a
        Grade.

        """
        return self._find_all('grades', attributes)

    def update_grade(self, grade):
        """Update a grade.

        Parameters
        ----------
        grade: nbgrader.api.Grade
            The grade to update.

        """
        self._update('grades', grade)

    #### Comments

    def find_or_create_comment(self, **attributes):
        """Look up or create a comment by its associated attributes. For
        example:

        >>> gb = Commentbook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> notebook = gb.find_notebook(notebook_id="Problem 1", student=student)
        >>> gb.find_or_create_comment(comment_id="foo", notebook=notebook)

        will find a comment with id "foo" and with an associated
        notebook whose id is "Problem 1" and whose student has id
        "Hacker". If there is more than one matching comment, then an
        error will be thrown.

        If there are no matching comments, then a new comment will be
        created with the given attributes.

        Valid keyword arguments correspond to the attributes for a
        Comment.

        """
        return self._find_or_create('comments', attributes)

    def find_comment(self, **attributes):
        """Look up a comment by its associated attributes. For example:

        >>> gb = Commentbook("example")
        >>> student = gb.find_student(student_id="Hacker")
        >>> notebook = gb.find_notebook(notebook_id="Problem 1", student=student)
        >>> gb.find_comment(comment_id="foo", notebook=notebook)

        will find a comment with id "foo" and with an associated
        notebook whose id is "Problem 1" and whose student has id
        "Hacker". If there is more than one matching comment, then an
        error will be thrown.

        Valid keyword arguments correspond to the attributes for a
        Comment.

        """
        comment = self._find('comments', attributes)
        if comment is None:
            raise ValueError('no such comment: {}'.format(attributes))
        return comment

    def find_comments(self, **attributes):
        """Find all comments matching the given attributes. For example:

        >>> gb = Commentbook("example")
        >>> gb.find_comments(comment_id="foo")

        will find all comment with id "foo".

        Valid keyword arguments correspond to the attributes for a
        Comment.

        """
        return self._find_all('comments', attributes)

    def update_comment(self, comment):
        """Update a comment.

        Parameters
        ----------
        comment: nbgrader.api.Comment
            The comment to update.

        """
        self._update('comments', comment)

    def get_assignment_notebooks(self, assignment):
        notebooks = {}
        for notebook in self.find_notebooks(assignment=assignment):
            if notebook.notebook_id not in notebooks:
                notebooks[notebook.notebook_id] = []
            notebooks[notebook.notebook_id].append(notebook)
        return notebooks

    def notebook_score(self, notebook):
        grades = self.find_grades(notebook=notebook)
        score = {"score": 0, "max_score": 0, "needs_manual_grade": False}
        for grade in grades:
            if grade.score is not None:
                score["score"] += grade.score
            elif grade.autoscore is not None:
                score["score"] += grade.autoscore
            else:
                score["needs_manual_grade"] = True
            if grade.max_score is not None:
                score["max_score"] += grade.max_score
        return score

    def assignment_score(self, assignment, student):
        notebooks = self.find_notebooks(assignment=assignment, student=student)
        if len(notebooks) == 0:
            return None

        score = {"score": 0, "max_score": 0, "needs_manual_grade": False}
        for nb in notebooks:
            nb_score = self.notebook_score(nb)
            score["score"] += nb_score["score"]
            score["max_score"] += nb_score["max_score"]
            if nb_score["needs_manual_grade"]:
                score["needs_manual_grade"] = True
        return score

    def avg_notebook_scores(self, assignment):
        all_scores = []
        assignment_notebooks = self.get_assignment_notebooks(assignment)
        notebook_ids = sorted(assignment_notebooks.keys())
        for notebook_id in notebook_ids:
            notebooks = assignment_notebooks[notebook_id]
            scores = [self.notebook_score(nb) for nb in notebooks]
            avg_score = sum([s["score"] for s in scores]) / float(len(scores))
            max_score = set([s["max_score"] for s in scores])
            assert len(max_score) == 1
            all_scores.append({
                "notebook_id": notebook_id,
                "avg_score": avg_score,
                "max_score": list(max_score)[0]
            })
        return all_scores

    def avg_assignment_score(self, assignment):
        scores = [self.assignment_score(assignment, student) for student in self.students]
        scores = [s for s in scores if s is not None]
        if len(scores) > 0:
            avg_score = sum([s["score"] for s in scores]) / float(len(scores))
            max_score = set([s["max_score"] for s in scores])
        else:
            avg_score = 0
            max_score = set([0])
        assert len(max_score) == 1
        all_scores = {
            "avg_score": avg_score,
            "max_score": list(max_score)[0]
        }
        return all_scores

    def student_score(self, student):
        scores = [self.assignment_score(assignment, student) for assignment in self.assignments]
        scores = [s for s in scores if s is not None]
        score = sum([s["score"] for s in scores])
        max_score = sum([s["max_score"] for s in scores])
        all_scores = {
            "score": score,
            "max_score": max_score
        }
        return all_scores
