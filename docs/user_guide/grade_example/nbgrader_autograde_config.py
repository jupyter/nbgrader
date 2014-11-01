c = get_config()

import os
c.AutogradeApp.notebooks = ['submitted/*.ipynb']
c.FilesWriter.build_directory = os.path.join(os.getcwd(), 'autograded')
c.FindStudentID.regexp = r".*/submitted/Problem [0-9] (?P<student_id>.+).ipynb"
c.SaveAutoGrades.assignment_id = "Problem Set 1"
c.SaveAutoGrades.db_name = "example"
