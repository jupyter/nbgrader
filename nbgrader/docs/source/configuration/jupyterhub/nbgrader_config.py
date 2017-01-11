import os

c = get_config()

## Generic nbgrader options (technically, the exchange directory is not used
## by the formgrader, but it is left in here for consistency with the rest of
## the user guide):

c.NbGrader.course_id = "course101"
c.TransferApp.exchange_directory = "/tmp/exchange"
c.NbGrader.db_assignments = [dict(name="ps1", duedate="2015-02-02 17:00:00 UTC")]
c.NbGrader.db_students = [
    dict(id="bitdiddle", first_name="Ben", last_name="Bitdiddle"),
    dict(id="hacker", first_name="Alyssa", last_name="Hacker"),
    dict(id="reasoner", first_name="Louis", last_name="Reasoner")
]

## Options that are specific to the formgrader and integrating it with JupyterHub:

c.FormgradeApp.ip = "127.0.0.1"
c.FormgradeApp.port = 9000
c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"

# The grader_group option is the most important option that must be specified:
# it determines who will be able to access the formgrader, and corresponds to a
# JupyterHub group (specified in the JupyterHub.load_groups config option).
c.HubAuth.grader_group = "course101-graders"

# Change this to be the path to the user guide folder in your clone of
# nbgrader, or just wherever you have your class files. This is relative
# to the root of the notebook server launched by JupyterHub, which is
# probably your home directory. This is used for accessing the *live*
# version of notebooks via JupyterHub. If you don't want to access the
# live notebooks and are fine with just the static interface provided by
# the formgrader, then you can ignore this option.
c.HubAuth.notebook_url_prefix = "path/to/class_files"

# Only one user is able to access the *live* autograded notebooks, which is the
# user who actually owns those files (all other users, even if they have access
# to the formgrader, will be unable to access the live notebooks). The
# notebook_server_user option should be set to the username of this user if they
# want to be able to access the live notebooks. If you don't want to access the
# live notebooks and are fine with just the static interface provided by the
# formgrader, then you can ignore this option.
c.HubAuth.notebook_server_user = "instructor1"
