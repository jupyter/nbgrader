c = get_config()

c.AssignApp.notebooks = ['teacher/*.ipynb']
c.FilesWriter.build_directory = 'student'
c.IncludeHeaderFooter.header = 'header.ipynb'

# These are only used if run with --save-cells
c.SaveGradeCells.assignment_id = "Problem Set 1"
c.SaveGradeCells.db_url = "sqlite:////tmp/nbgrader_example.db"
