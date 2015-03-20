c = get_config()

c.FormgradeApp.base_directory = "autograded"
c.FormgradeApp.directory_format = "{student_id}/{notebook_id}.ipynb"
c.FormgradeApp.db_url = "sqlite:////../nbgrader_example.db"
