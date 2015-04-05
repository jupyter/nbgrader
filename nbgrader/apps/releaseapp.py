import os
import shutil
import datetime
from dateutil.tz import gettz

from textwrap import dedent

from IPython.utils.traitlets import Unicode, List, Bool
from IPython.config.application import catch_config_error

from nbgrader.apps.baseapp import BaseNbGraderApp, nbgrader_aliases, nbgrader_flags
from nbgrader.utils import check_mode, check_directory, get_username, self_owned, find_owner

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "SubmitApp.timezone"
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'force': (
        {'ReleaseApp' : {'force' : True}},
        "Force overwrite of existing files in the exchange."
    ),
    'remove': (
        {'ReleaseApp' : {'remove': True}},
        "Only remove existing files in the exchange."
    ),
})


class ReleaseApp(BaseNbGraderApp):

    name = u'nbgrader-release'
    description = u'Release an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Here we go...
        """

    timezone = Unicode(
        "UTC", config=True,
        help="Timezone for recording timestamps")

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z", config=True,
        help="Format string for timestamps")
    
    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__"
        ],
        config=True,
        help=dedent(
            """
            List of file names or file globs to be ignored when creating the
            submission.
            """
        )
    )

    force = Bool(False, config=True, help="Force overwrite existing files in the exchange.")

    remove = Bool(False, config=True, help="Only remove existing files in the exchange.")
    
    exchange_directory = Unicode("/srv/nbgrader/exchange", config=True)
    
    current_username = Unicode(get_username())

    def _current_username_changed(self, name, new):
        self.course_key = self._compute_course_key(new, self.course_id)
    
    course_key = Unicode('', config=True, help="A key that is unique per instructor and course.")
    
    def _course_key_default(self):
        return self._compute_course_key(self.current_username, self.course_id)

    def _course_id_changed(self, name, new):
        self.course_key = self._compute_course_key(self.current_username, new)
    
    def _compute_course_key(self, username, course_id):
        return username + '-' + course_id
    
    def init_assignment(self):
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
    
    def ensure_exchange_directory(self):
        """See if the exchange directory exists and is writable, raise if not."""
        if not check_directory(self.exchange_directory, write=True, execute=True):
            self.log.error("Unwritable directory, please contact your instructor: {}".format(self.exchange_directory))
            sys.exit(1)

    def set_timestamp(self):
        """Set the timestap."""
        tz = gettz(self.timezone)
        if tz is None:
            self.log.error("Invalid timezone: {}".format(self.timezone))
            sys.exit(1)
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)
        
    @catch_config_error
    def initialize(self, argv=None):
        super(BaseNbGraderApp, self).initialize(argv)
        self.init_assignment()
        self.ensure_exchange_directory()
        self.set_timestamp()

    def init_src(self):
        self.src_path = os.path.abspath(os.path.join(self.release_directory, self.assignment_id))
        if not os.path.isdir(self.src_path):
            self.log.error("Assignment not found: {}/{}".format(self.release_directory, self.assignment_id))
            self.fail("You have to run `nbgrader release` from your main nbgrader directory.")
        self.log.debug("src_path: {}".format(self.src_path))
        self.log.debug("assignment_id: {}".format(self.assignment_id))
        self.log.debug("course_id: {}".format(self.course_id))
    
    def init_dest(self):
        self.course_key_path = os.path.join(self.exchange_directory, self.course_key)
        self.outbound_path = os.path.join(self.course_key_path, 'outbound')
        self.inbound_path = os.path.join(self.course_key_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path, self.assignment_id)
        self.log.debug("course_key: {}".format(self.course_key))
        self.log.debug("dest_path: {}".format(self.dest_path))

    def ensure_directory(self, path, mode):
        """Ensure that the path exists, has the right mode and is self owned."""
        if not os.path.isdir(path):
            os.mkdir(path)
            # For some reason, Python won't create a directory with a mode of 0o733
            # so we have to create and then chmod.
            os.chmod(path, mode)
        else:
            if not self_owned(path):
                self.log.error("You don't own the directory: {}".format(path))
                sys.exit(1)
    
    def ensure_directories(self):
        """Ensure the dest directories exist and have the right mode/owner."""
        self.ensure_directory(self.course_key_path, 0o755)
        self.ensure_directory(self.outbound_path, 0o755)
        self.ensure_directory(self.inbound_path, 0o733)

    def copy_files(self):
        if self.remove:
            if os.path.isdir(self.dest_path):
                self.log.info("Removing old files: {} {}".format(self.course_key, self.assignment_id))
                shutil.rmtree(self.dest_path)
            else:
                self.log.info("No existing files exist for: {} {}".format(self.course_key, self.assignment_id))
        else:
            if os.path.isdir(self.dest_path):
                if self.force:
                    self.log.info("Overwriting files: {} {}".format(self.course_key, self.assignment_id))
                    shutil.rmtree(self.dest_path)
                else:
                    self.fail("Destination already exists, add --force to overwrite: {} {}".format(self.course_key, self.assignment_id))
            shutil.copytree(self.src_path, self.dest_path, ignore=shutil.ignore_patterns(*self.ignore))
            self.log.info("Source: {}".format(self.src_path))
            self.log.info("Destination: {}".format(self.dest_path))
            self.log.info("Released as: {} {}".format(self.course_key, self.assignment_id))
            
    def start(self):
        super(BaseNbGraderApp, self).start() 
        self.init_src()
        self.init_dest()
        self.ensure_directories()
        self.copy_files()

