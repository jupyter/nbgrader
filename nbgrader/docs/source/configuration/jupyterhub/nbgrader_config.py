import os

c = get_config()

## Generic nbgrader options (technically, the exchange directory is not used
## by the formgrader, but it is left in here for consistency with the rest of
## the user guide):

c.NbGrader.course_id = "example_course"
c.TransferApp.exchange_directory = "/tmp/exchange"
c.NbGrader.db_assignments = [dict(name="ps1", duedate="2015-02-02 17:00:00 UTC")]
c.NbGrader.db_students = [
    dict(id="bitdiddle", first_name="Ben", last_name="Bitdiddle"),
    dict(id="hacker", first_name="Alyssa", last_name="Hacker"),
    dict(id="reasoner", first_name="Louis", last_name="Reasoner")
]

## Options that are specific to the formgrader and integrating it with JuptyerHub:

c.FormgradeApp.ip = "127.0.0.1"
c.FormgradeApp.port = 9000
c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"

# This is the actual URL or public IP address where JupyterHub is running (by
# default, the HubAuth will just use the same address as what the formgrader is
# running on -- so in this case, 127.0.0.1). If you have JupyterHub behind a
# domain name, you probably want to set that here.
c.HubAuth.hub_address = "127.0.0.1"

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

# This loads the environment variable containing the hubapi token that we will
# generate by running the `jupyterhub token <name>` command, just before we
# actually launch the formgrader.
c.HubAuth.hubapi_token = os.environ['JPY_API_TOKEN']
