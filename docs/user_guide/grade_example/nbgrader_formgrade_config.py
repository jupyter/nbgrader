c = get_config()

c.FormgradeApp.notebooks = ['autograded/*.ipynb']
c.FindStudentID.regexp = r".*/autograded/Problem [0-9] (?P<student_id>.+).ipynb"
c.ServeFormGrader.base_directory = 'autograded'
