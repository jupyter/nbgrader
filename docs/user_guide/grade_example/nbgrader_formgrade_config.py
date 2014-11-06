c = get_config()

c.FormgradeApp.base_directory = "autograded"
c.FormgradeApp.db_name = "example"
c.FormgradeApp.directory_format = "{student_id}/{notebook_id}.ipynb"
