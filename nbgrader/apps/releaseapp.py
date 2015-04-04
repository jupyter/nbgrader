import os
import pwd
import shutil
import datetime
from dateutil.tz import gettz
import uuid

from textwrap import dedent

from IPython.utils.traitlets import Unicode, List
from IPython.config.application import catch_config_error

from nbgrader.apps.baseapp import BaseApp, base_aliases, base_flags

aliases = {}
aliases.update(base_aliases)
aliases.update({
    "timezone": "SubmitApp.timezone"
})

flags = {}
flags.update(base_flags)


def get_username():
    """Get the username of the current process."""
    return pwd.getpwuid(os.getuid())[0]


class PushApp(BaseApp):

    name = u'nbgrader-push'
    description = u'Push a directory to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        To publish an assignment as an instructor:
            nbgrader push "Problem Set 1" instructor_username.phys202

        to turn in an assignment as a student:
            nbgrader push "Problem Set 1" instructor_username.phys202
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

    exchange_directory = Unicode("/srv/nbgrader/exchange", config=True)
    
    current_username = Unicode(get_username())
    
    @property
    def outbound(self):
        """Is push being used in outbound mode.
        
        The `nbgrader push` command runs in two different modes:
        
        1. In outbound mode, an instructor is distributing an assignment to
           students.
        2. In inbound mode, a student is turning in an assignent to an
           instructor.
           
        The two modes are distinguished by whether or not the src (current)
        and dest usernames are the same (same=outbound).
        """
        return self.src_username == self.dest_username
    
    def check_mode(self, path, read=False, write=False, execute=False):
        """Can the current user can rwx the path."""
        mode = 0
        if read:
            mode |= os.R_OK
        if write:
            mode |= os.W_OK
        if execute:
            mode |= os.X_OK
        return os.access(path, mode)
    
    def check_directory(self, path, read=False, write=False, execute=False):
        """Does that path exist and can the current user rwx."""
        if os.path.isdir(path) and self.check_mode(path, read=read, write=write, execute=execute):
            return True
        else:
            return False

    def ensure_exchange_directory(self):
        """See if the exchange directory exists and is writable, raise if not."""
        if not self.check_directory(self.exchange_directory, write=True, execute=True):
            raise IOError("Unwritable directory, please contact your instructor: {}".format(self.exchange_directory))

    def set_timestamp(self):
        """Set the timestap."""
        tz = gettz(self.timezone)
        if tz is None:
            raise ValueError("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)
        
    @catch_config_error
    def initialize(self, argv=None):
        super(PushApp, self).initialize(argv)
        self.ensure_exchange_directory()
        self.set_timestamp()

    def parse_src(self):
        """Parse the src argument, which is the directory/assignment to be copied."""
        raw_src = self.extra_args[0]
        self.src_path = os.path.abspath(raw_src)
        self.assignment_id = os.path.split(self.src_path)[-1]
        self.src_username = self.current_username
        if not os.path.isdir(self.src_path):
            raise ValueError("The source directory doesn't exist: {}".format(raw_src))
        self.log.debug("src_username: {}".format(self.src_username))
        self.log.debug("src_path: {}".format(self.src_path))
        self.log.debug("assignment_id: {}".format(self.assignment_id))
        self.log.info("Source: username={} assignment={}".format(self.src_username, self.src_path))
        
    def parse_dest(self):
        """Parse the dest argument, which is a dotted username.course_id."""
        raw_dest = self.extra_args[1]
        dest_args = raw_dest.split('.')
        if len(dest_args) != 2:
            raise ValueError("Destination not provided in username.course format: {}".format(raw_dest))
        self.dest_username = dest_args[0]
        self.course_id = dest_args[1]
        self.dest_username_path = os.path.join(self.exchange_directory, self.dest_username)
        self.course_id_path = os.path.join(self.dest_username_path, self.course_id)
        self.outbound_path = os.path.join(self.course_id_path, 'outbound')
        self.inbound_path = os.path.join(self.course_id_path, 'inbound')
        self.log.debug("dest_username: {}".format(self.dest_username))
        self.log.debug("course_id: {}".format(self.course_id))
        self.log.info("Destination: username={} and course={}".format(self.dest_username, self.course_id))
    
    def parse_src_dest(self):
        if len(self.extra_args) != 2:
            raise ValueError("You must provide a source and target.")
        self.parse_src()
        self.parse_dest()
    
    def ensure_directories(self):        
        if self.outbound:
            if not os.path.isdir(self.dest_username_path):
                os.mkdir(self.dest_username_path, 0o755)
            if not os.path.isdir(self.course_id_path):
                os.mkdir(self.course_id_path, 0o755)
            if not os.path.isdir(self.outbound_path):
                os.mkdir(self.outbound_path, 0o755)
            if not os.path.isdir(self.inbound_path):
                os.mkdir(self.inbound_path, 0o733)
        else:
            if not os.path.isdir(self.dest_username_path):
                raise ValueError("User doesn't exist: {}".format(self.dest_username))
            if not os.path.isdir(self.course_id_path):
                raise ValueError("Course doesn't exist: {}".format(self.course_id))
            if not os.path.isdir(self.inbound_path):
                raise ValueError("Inbound path not found, please see your instructor: {}".format(self.inbound_path))
            if not self.check_mode(self.inbound_path, write=True, execute=True):
                raise ValueError("Incorrect permissions on inbound path, please see your instructor: {}".format(self.inbound_path))
            
    
    def calculate_dest_path(self):
        if self.outbound:
            self.dest_path = os.path.join(self.outbound_path, self.assignment_id)
        else:
            # If inbound, we save the assignment directory with the username, the assignment_id and
            # a uuid. The uuid prevents students from overwriting other students submission.
            self.dest_assignment_id = '-'.join([self.src_username, self.assignment_id, uuid.uuid4()])
            self.dest_path = os.path.join(self.inbound_path, self.dest_assignment_id)
        self.log.debug("dest_path: {}".format(self.dest_path))

    
    def do_copy(self, src, dest):
        """Copy the src directory to (not in) the dest directory.
        
        This works recursively and will ignore the globs defined in self.ignore.
        """
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.ignore))
        self.log.debug("Copying {} -> {}".format(src, dest))
    
    def copy_files(self):
        self.do_copy(self.src_path, self.dest_path)

        # If inbound, save the timestamp in a file for the autograder.
        if not self.outbound:
            with open(os.path.join(self.dest_path, "timestamp.txt"), "w") as fh:
                fh.write(self.timestamp)

    def start(self):
        super(PushApp, self).start()        
        self.parse_src_dest()
        self.ensure_directories()
        self.calculate_dest_path()
        self.copy_files()

