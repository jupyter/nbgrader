import json
from uuid import uuid4
from pymongo import MongoClient


class Document(object):

    _defaults = {}

    def __init__(self, **kwargs):
        if '_id' in kwargs:
            self._id = kwargs['_id']
        else:
            self._id = str(uuid4())
        for field, default_value in self._defaults.items():
            setattr(self, field, kwargs.get(field, default_value))

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
        'grades': Grade,
        'comments': Comment,
        'students': Student,
        'notebooks': Notebook,
        'assignments': Assignment
    }

    def __init__(self, ip="localhost", port=27017):
        self.client = MongoClient(ip, port)
        self.db = self.client['gradebook']

    def _add(self, collection, document):
        self.db[collection].insert(document.to_dict())

    def _update(self, collection, document):
        _id = {"_id": document._id}
        self.db[collection].update(_id, {"$set": document.to_dict()})

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

    def find_grades(self, **query):
        return self._find_all('grades', query)

    def find_grade(self, **query):
        grade = self._find('grades', query)
        if grade is None:
            raise ValueError('no such grade: {}'.format(query))
        return grade

    def find_or_create_grade(self, **query):
        return self._find_or_create('grades', query)

    def update_grade(self, grade):
        self._update('grades', grade)

    def find_comments(self, **query):
        return self._find_all('comments', query)

    def find_comment(self, **query):
        comment = self._find('comments', query)
        if comment is None:
            raise ValueError('no such comment: {}'.format(query))
        return comment

    def update_comment(self, comment):
        self._update('comments', comment)

    def find_or_create_comment(self, **query):
        return self._find_or_create('comments', query)

    def find_student(self, **query):
        student = self._find('students', query)
        if student is None:
            raise ValueError('no such student: {}'.format(query))
        return student

    def add_student(self, student):
        return self._add('students', student)

    @property
    def students(self):
        return self._find_all('students', {})

    def add_notebook(self, notebook):
        return self._add('notebooks', notebook)

    def find_notebook(self, **query):
        notebook = self._find('notebooks', query)
        if notebook is None:
            raise ValueError('no such notebook: {}'.format(query))
        return notebook

    def find_or_create_notebook(self, **query):
        return self._find_or_create('notebooks', query)

    @property
    def notebooks(self):
        return self._find_all('notebooks', {})

    def add_assignment(self, assignment):
        return self._add('assignments', assignment)

    @property
    def assignments(self):
        return self._find_all('assignments', {})

    def find_assignment(self, **query):
        assignment = self._find('assignments', query)
        if assignment is None:
            raise ValueError('no such assignment: {}'.format(query))
        return assignment
