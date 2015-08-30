c = get_config()

## Generic nbgrader options (technically, the exchange directory is not used
## by the formgrader, but it is left in here for consistency with the rest of
## the user guide):

c.NbGrader.course_id = "example_course"
c.TransferApp.exchange_directory = "/tmp/exchange"

## Options that are specific to the formgrader and integrating it with JuptyerHub:

c.FormgradeApp.ip = "127.0.0.1"
c.FormgradeApp.port = 9000
c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"

# Change this to be the path to the user guide folder in your clone of
# nbgrader, or just wherever you have your class files. This is relative
# to the root of the notebook server launched by JupyterHub, which is
# probably your home directory. This is used for accessing the *live*
# version of notebooks via JupyterHub. If you don't want to access the
# live notebooks and are fine with just the static interface provided by
# the formgrader, then you can ignore this option.
c.HubAuth.notebook_url_prefix = "path/to/class_files"

# Change this to be the list of unix usernames that are allowed to access
# the formgrader.
c.HubAuth.graders = ["instructor1", "instructor2"]

# This specifies that the formgrader should automatically generate an api
# token to authenticate itself with JupyterHub.
c.HubAuth.generate_hubapi_token = True

# Change this to be the jupyterhub.sqlite located in the directory where
# you actually run JupyterHub.
c.HubAuth.hub_db = "path/to/jupyterhub.sqlite"
