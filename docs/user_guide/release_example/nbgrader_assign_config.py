c = get_config()

import os
cwd = os.getcwd()

c.AssignApp.notebooks = ['teacher/*.ipynb']
c.AssignApp.output_dir = os.path.join(cwd, 'student')
c.IncludeHeaderFooter.header = os.path.join(cwd, 'header.ipynb')

# These are only used if run with --save
c.SaveGradeCells.assignment_id = "Problem Set 1"
c.SaveGradeCells.db_name = "example"
