c = get_config()

c.AutogradeApp.notebooks = ['StudentNotebookBitdiddle.ipynb']
c.AutogradeApp.output_base = 'GradedNotebookBitdiddle'
c.FindStudentID.regexp = r".*/StudentNotebook(?P<student_id>.+).ipynb"
