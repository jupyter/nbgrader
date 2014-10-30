c = get_config()

c.FormgradeApp.notebooks = ['StudentNotebook*.autograded.ipynb']
c.FindStudentID.regexp = ".*/StudentNotebook(?P<student_id>.+).autograded.ipynb"
