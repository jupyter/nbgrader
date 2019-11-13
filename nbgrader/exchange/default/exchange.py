import os
import datetime
import sys
import shutil
import glob

from textwrap import dedent

from traitlets import Unicode, Bool, default
from jupyter_core.paths import jupyter_data_dir

from nbgrader.exchange.abc import Exchange as ABCExchange
from nbgrader.exchange import ExchangeError
from nbgrader.utils import check_directory, ignore_patterns, self_owned


class Exchange(ABCExchange):
    assignment_dir = Unicode(
        ".",
        help=dedent(
            """
            Local path for storing student assignments.  Defaults to '.'
            which is normally Jupyter's notebook_dir.
            """
        )
    ).tag(config=True)

    root = Unicode(
        "/srv/nbgrader/exchange",
        help="The nbgrader exchange directory writable to everyone. MUST be preexisting."
    ).tag(config=True)

    cache = Unicode(
        "",
        help="Local cache directory for nbgrader submit and nbgrader list. Defaults to $JUPYTER_DATA_DIR/nbgrader_cache"
    ).tag(config=True)

    @default("cache")
    def _cache_default(self):
        return os.path.join(jupyter_data_dir(), 'nbgrader_cache')

    path_includes_course = Bool(
        False,
        help=dedent(
            """
            Whether the path for fetching/submitting  assignments should be
            prefixed with the course name. If this is `False`, then the path
            will be something like `./ps1`. If this is `True`, then the path
            will be something like `./course123/ps1`.
            """
        )
    ).tag(config=True)

    def set_perms(self, dest, fileperms, dirperms):
        all_dirs = []
        for dirname, _, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), fileperms)
            all_dirs.append(dirname)

        for dirname in all_dirs[::-1]:
            os.chmod(dirname, dirperms)

    def ensure_root(self):
        """See if the exchange directory exists and is writable, fail if not."""
        if not check_directory(self.root, write=True, execute=True):
            self.fail("Unwritable directory, please contact your instructor: {}".format(self.root))

    def init_src(self):
        """Compute and check the source paths for the transfer."""
        raise NotImplementedError

    def init_dest(self):
        """Compute and check the destination paths for the transfer."""
        raise NotImplementedError

    def copy_files(self):
        """Actually do the file transfer."""
        raise NotImplementedError

    def do_copy(self, src, dest, log=None):
        """
        Copy the src dir to the dest dir, omitting excluded
        file/directories, non included files, and too large files, as
        specified by the options coursedir.ignore, coursedir.include
        and coursedir.max_file_size.
        """
        shutil.copytree(src, dest,
                        ignore=ignore_patterns(exclude=self.coursedir.ignore,
                                               include=self.coursedir.include,
                                               max_file_size=self.coursedir.max_file_size,
                                               log=self.log))
        # copytree copies access mode too - so we must add go+rw back to it if
        # we are in groupshared.
        if self.coursedir.groupshared:
            for dirname, _, filenames in os.walk(dest):
                # dirs become ug+rwx
                st_mode = os.stat(dirname).st_mode
                if st_mode & 0o2770 != 0o2770:
                    try:
                        os.chmod(dirname, (st_mode|0o2770) & 0o2777)
                    except PermissionError:
                        self.log.warning("Could not update permissions of %s to make it groupshared", dirname)

                for filename in filenames:
                    filename = os.path.join(dirname, filename)
                    st_mode = os.stat(filename).st_mode
                    if st_mode & 0o660 != 0o660:
                        try:
                            os.chmod(filename, (st_mode|0o660) & 0o777)
                        except PermissionError:
                            self.log.warning("Could not update permissions of %s to make it groupshared", filename)

    def start(self):
        if sys.platform == 'win32':
            self.fail("Sorry, the exchange is not available on Windows.")
        if not self.coursedir.groupshared:
            # This just makes sure that directory is o+rwx.  In group shared
            # case, it is up to admins to ensure that instructors can write
            # there.
            self.ensure_root()

        super(Exchange, self).start()

    def _assignment_not_found(self, src_path, other_path):
        msg = "Assignment not found at: {}".format(src_path)
        self.log.fatal(msg)
        found = glob.glob(other_path)
        if found:
            # Normally it is a bad idea to put imports in the middle of
            # a function, but we do this here because otherwise fuzzywuzzy
            # prints an annoying message about python-Levenshtein every
            # time nbgrader is run.
            from fuzzywuzzy import fuzz
            scores = sorted([(fuzz.ratio(self.src_path, x), x) for x in found])
            self.log.error("Did you mean: %s", scores[-1][1])

        raise ExchangeError(msg)

    def ensure_directory(self, path, mode):
        """Ensure that the path exists, has the right mode and is self owned."""
        if not os.path.isdir(path):
            os.makedirs(path)
            # For some reason, Python won't create a directory with a mode of 0o733
            # so we have to create and then chmod.
            os.chmod(path, mode)
        else:
            if not self.coursedir.groupshared and not self_owned(path):
                self.fail("You don't own the directory: {}".format(path))
