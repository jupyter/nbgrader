c = get_config()

import os
db_url = os.path.abspath(os.path.join(os.getcwd(), "..", "nbgrader_example.db"))

c.FormgradeApp.base_directory = "autograded"
c.FormgradeApp.directory_format = "{student_id}/{notebook_id}.ipynb"
c.FormgradeApp.db_url = "sqlite:///{}".format(db_url)
