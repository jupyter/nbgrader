c = get_config()

c.NbGraderConfig.course_id = "example_course"

c.FormgradeApp.ip = "127.0.0.1"
c.FormgradeApp.port = 9000
c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"

# Change this to be the path to the user guide folder in your clone of
# nbgrader, or just wherever you have your class files. This is relative
# to the root of the notebook server launched by JupyterHub, which is
# probably your home directory.
c.HubAuth.notebook_url_prefix = "path/to/class_files"

# Change this to be the list of unix usernames that are allowed to access
# the formgrader.
c.HubAuth.graders = ["jhamrick"]

# This specifies that the formgrader should automatically generate an api
# token to authenticate itself with JupyterHub.
c.HubAuth.generate_hubapi_token = True

# Change this to be the jupyterhub.sqlite located in the directory where
# you actually run JupyterHub.
c.HubAuth.hub_db = "path/to/jupyterhub.sqlite"
