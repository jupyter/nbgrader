c = get_config()

c.FormgradeApp.notebooks = ['GradedNotebookBitdiddle.ipynb']
c.FindStudentID.regexp = ".*/GradedNotebook(?P<student_id>.+).ipynb"
