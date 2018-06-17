from nbgrader.apps import NbGraderAPI
from nbgrader import coursedir
from nbgrader.api import SubmittedNotebook,Grade,GradeCell,Notebook,Assignment,Student,SubmittedAssignment,BaseCell,SolutionCell,TaskCell
from sqlalchemy import select, func, exists,case
from sqlalchemy.orm import aliased
from sqlalchemy.sql import  and_,or_

cd=coursedir.CourseDirectory(root='/home/daniel/Teaching/L2python')

api=NbGraderAPI(cd)

api.exchange='/home/daniel/Teaching/L2python/exchange'
#print (api.get_submissions('a_a'))

notebook_id='Assignment 1'
assignment_id='a_0_a'
nb=api.gradebook.find_submission_notebook_by_id('2187fae4185340499e028eb98c0b25c4')


res=select([case([
    (BaseCell.type=='GradeCell',GradeCell.max_score),
    (BaseCell.type=='TaskCell',TaskCell.max_score),
    (BaseCell.type=='SolutionCell','S'),
    ])]).where(
        or_(
            and_(TaskCell.id==BaseCell.id,BaseCell.type=='TaskCell'),            
            and_(GradeCell.id==BaseCell.id,BaseCell.type=='GradeCell')
        )
    )

print(res)

res2=select([case([
    (BaseCell.type=='GradeCell','G'),
    (BaseCell.type=='TaskCell','T'),
    (BaseCell.type=='SolutionCell','S'),
    ])])



res3=select([func.sum(GradeCell.max_score).label('total')]).where('69fb401a0e1846d2953cf536e37d2e44' == GradeCell.id)
res4=select([func.sum(TaskCell.max_score).label('total')]).where('69fb401a0e1846d2953cf536e37d2e44' == TaskCell.id)
res5=res3.union_all(res4)
res5a=aliased(res5)

res6=select([func.sum(res5a.c.total)])

r=api.gradebook.db.execute(res)
r2=api.gradebook.db.execute(res2)
r3=api.gradebook.db.execute(res3)
r4=api.gradebook.db.execute(res4)

r5=api.gradebook.db.execute(res5)
r6=api.gradebook.db.execute(res6)

print(len(list(r)))
print(list(r2))
print(list(r3))
print(list(r4))
print(list(r5))
print(list(r6))

#print(list(api.gradebook.db.execute(
#    select([Grade.id,Grade.max_score]))))

print (res3)