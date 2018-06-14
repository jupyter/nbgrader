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
nb=api.gradebook.find_submission_notebook_by_id('2187fae4185340499e028eb98c0b25c4')

print ([g.to_dict() for g in  nb.grades])
