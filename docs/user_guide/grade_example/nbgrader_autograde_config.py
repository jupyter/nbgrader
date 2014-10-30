c = get_config()

import glob
c.AutogradeApp.notebooks = [x for x in glob.glob("StudentNotebook*.ipynb") if not x.endswith(".autograded.ipynb")]
c.Exporter.file_extension = 'autograded.ipynb'
c.FindStudentID.regexp = r".*/StudentNotebook(?P<student_id>.+).ipynb"
