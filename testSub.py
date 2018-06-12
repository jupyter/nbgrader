from nbgrader.apps import NbGraderAPI
from nbgrader import coursedir

cd=coursedir.CourseDirectory(root='/home/daniel/Teaching/L2python')

api=NbGraderAPI(cd)

api.exchange='/home/daniel/Teaching/L2python/exchange'
print (api.get_submissions('bbbbbbbbb'))
