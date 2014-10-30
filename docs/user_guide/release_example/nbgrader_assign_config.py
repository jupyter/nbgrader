c = get_config()

import os
cwd = os.getcwd()

c.AssignApp.notebooks = ['teacher/*.ipynb']
c.FilesWriter.build_directory = os.path.join(cwd, 'student')
c.IncludeHeaderFooter.header = os.path.join(cwd, 'header.ipynb')
