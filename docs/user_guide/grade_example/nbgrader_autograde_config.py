c = get_config()

import os
c.AutogradeApp.notebooks = ['submitted']
c.AutogradeApp.output_dir = os.path.join(os.getcwd(), 'autograded')
c.AutogradeApp.recursive = True
c.FindStudentID.regexp = r"submitted/(?P<student_id>.+)/.*.ipynb"
c.SaveAutoGrades.assignment_id = "Problem Set 1"
c.SaveAutoGrades.db_name = "example"
