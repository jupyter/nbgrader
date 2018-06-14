from nbgrader.apps import NbGraderAPI
from nbgrader import coursedir
from nbgrader.api import SubmittedNotebook,Grade,GradeCell,Notebook,Assignment,Student,SubmittedAssignment,BaseCell
from sqlalchemy import select, func, exists
from sqlalchemy.sql import  and_

cd=coursedir.CourseDirectory(root='/home/daniel/Teaching/L2python')

api=NbGraderAPI(cd)

api.exchange='/home/daniel/Teaching/L2python/exchange'
#print (api.get_submissions('a_a'))

notebook_id='Assignment 1'
assignment_id='a_0_a'

res = api.gradebook.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("code_score"),
            func.sum(GradeCell.max_score).label("max_code_score"),
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "code")\
         .group_by(SubmittedNotebook.id)\
         .all()

print (res)

res = api.gradebook.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("written_score"),
            func.sum(GradeCell.max_score).label("max_written_score"),
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "markdown")\
         .group_by(SubmittedNotebook.id)\
         .all()
print (res)

manual_grade = api.gradebook.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.needs_manual_grade).label("needs_manual_grade")
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.needs_manual_grade)\
         .group_by(SubmittedNotebook.id)\
         .all()

        # subquery for failed tests
failed_tests = api.gradebook.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.failed_tests).label("failed_tests")
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.failed_tests)\
         .group_by(SubmittedNotebook.id)\
         .all()

print(manual_grade)
print (failed_tests)


ft=api.gradebook.db.query(
    Grade.auto_score, 
    Grade.max_score_gradecell,
    Grade.max_score_taskcell,
    Grade.cell_type_gradecell ,
    (Grade.cell_type_gradecell!=None)  & (Grade.auto_score < Grade.max_score_gradecell)  
        ).all()
print (ft)
#import sys
#sys.exit()

#api.gradebook.notebook_submission_dicts('Assessment 1', 'a_0_a')

code_scores = api.gradebook.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("code_score"),
            func.sum(GradeCell.max_score).label("max_code_score"),
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "code")\
         .group_by(SubmittedNotebook.id)\
         .subquery()
        #print(code_scores.all())

        # subquery for the written scores
written_scores = api.gradebook.db.query(
            SubmittedNotebook.id,
            func.sum(Grade.score).label("written_score"),
            func.sum(GradeCell.max_score).label("max_written_score"),
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .filter(GradeCell.cell_type == "markdown")\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # subquery for needing manual grading
manual_grade = api.gradebook.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.needs_manual_grade).label("needs_manual_grade")
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.needs_manual_grade)\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # subquery for failed tests
failed_tests = api.gradebook.db.query(
            SubmittedNotebook.id,
            exists().where(Grade.failed_tests).label("failed_tests")
        ).join(SubmittedAssignment, Assignment, Notebook)\
         .filter(
             Grade.notebook_id == SubmittedNotebook.id,
             Grade.failed_tests)\
         .group_by(SubmittedNotebook.id)\
         .subquery()

        # full query
_manual_grade = func.coalesce(manual_grade.c.needs_manual_grade, False)
_failed_tests = func.coalesce(failed_tests.c.failed_tests, False)
submissions = api.gradebook.db.query(
            SubmittedNotebook.id, Notebook.name,
            Student.id, Student.first_name, Student.last_name,
            func.sum(Grade.score), func.sum(GradeCell.max_score),
            code_scores.c.code_score, code_scores.c.max_code_score,
            written_scores.c.written_score, written_scores.c.max_written_score,
            _manual_grade, _failed_tests, SubmittedNotebook.flagged
        ).join(SubmittedAssignment, Notebook, Assignment, Student, Grade, GradeCell)\
         .outerjoin(code_scores, SubmittedNotebook.id == code_scores.c.id)\
         .outerjoin(written_scores, SubmittedNotebook.id == written_scores.c.id)\
         .outerjoin(manual_grade, SubmittedNotebook.id == manual_grade.c.id)\
         .outerjoin(failed_tests, SubmittedNotebook.id == failed_tests.c.id)\
         .filter(and_(
             Notebook.name == notebook_id,
             Assignment.name == assignment_id,
             Student.id == SubmittedAssignment.student_id,
             SubmittedAssignment.id == SubmittedNotebook.assignment_id,
             SubmittedNotebook.id == Grade.notebook_id,
             GradeCell.id == Grade.cell_id))\
         .group_by(
             SubmittedNotebook.id, Notebook.name,
             Student.id, Student.first_name, Student.last_name,
             code_scores.c.code_score, code_scores.c.max_code_score,
             written_scores.c.written_score, written_scores.c.max_written_score,
             _manual_grade, _failed_tests, SubmittedNotebook.flagged)\
         .all()
print (submissions)