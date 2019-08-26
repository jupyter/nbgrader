import os
import hashlib
import dateutil.parser
import glob
import six
import sys
import shutil
import stat
import logging
import traceback
import contextlib
import fnmatch

from setuptools.archive_util import unpack_archive
from setuptools.archive_util import unpack_tarfile
from setuptools.archive_util import unpack_zipfile
from tornado.log import LogFormatter
from dateutil.tz import gettz
from datetime import datetime

# pwd is for unix passwords only, so we shouldn't import it on
# windows machines
if sys.platform != 'win32':
    import pwd
else:
    pwd = None


def is_task(cell):
    """Returns True if the cell is a task cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('task', False)


def is_grade(cell):
    """Returns True if the cell is a grade cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('grade', False)


def is_solution(cell):
    """Returns True if the cell is a solution cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('solution', False)


def is_locked(cell):
    """Returns True if the cell source is locked (will be overwritten)."""
    if 'nbgrader' not in cell.metadata:
        return False
    elif is_solution(cell):
        return False
    elif is_grade(cell):
        return True
    else:
        return cell.metadata['nbgrader'].get('locked', False)

def get_partial_grade(output, max_points, log=None):
    # check that output["data"]["text/plain"] exists
    if not output["data"]["text/plain"]:
        raise KeyError("output ['data']['text/plain'] does not exist")
    grade = output["data"]["text/plain"]
    warning_msg = """For autograder tests, expecting output to indicate
    partial credit and be single value between 0.0 and max_points.
    Currently treating other output as full credit, but future releases
    may treat as error."""
    # For partial credit, expecting grade to be a value between 0 and max_points
    # A valid value for key output["data"]["text/plain"] can be a list or a string
    if (isinstance(grade,list)):
        if (len(grade)>1):
            if log:
                log.warning(warning_msg)
            return max_points
        grade = grade[0]
    try:
        grade = float(grade)
    except ValueError:
        if log:
            log.warning(warning_msg)
        return max_points
    if (grade > 0.0):
        if (grade > max_points):
            raise ValueError("partial credit cannot be greater than maximum points for cell")
        return grade
    else:
        if log:
            log.warning(warning_msg)
        return max_points

def determine_grade(cell, log=None):
    if not is_grade(cell):
        raise ValueError("cell is not a grade cell")

    max_points = float(cell.metadata['nbgrader']['points'])
    if is_solution(cell):
        # if it's a solution cell and the checksum hasn't changed, that means
        # they didn't provide a response, so we can automatically give this a
        # zero grade
        if "checksum" in cell.metadata.nbgrader and cell.metadata.nbgrader["checksum"] == compute_checksum(cell):
            return 0, max_points
        else:
            return None, max_points

    elif cell.cell_type == 'code':
        # for code cells, we look at the output. There are three options:
        # 1. output contains an error (no credit);
        # 2. output is a value greater than 0 (partial credit);
        # 3. output is something else, or nothing (full credit).
        for output in cell.outputs:
            # option 1: error, return 0
            if output.output_type == 'error':
                return 0, max_points
            # if not error, then check for option 2, partial credit
            if output.output_type == 'execute_result':
                # is there a single result that can be cast to a float?
                partial_grade = get_partial_grade(output, max_points, log)
                return partial_grade, max_points

        # otherwise, assume all fine and return all the points
        return max_points, max_points

    else:
        return None, max_points


def to_bytes(string):
    """A python 2/3 compatible function for converting a string to bytes.
    In Python 2, this just returns the 8-bit string. In Python 3, this first
    encodes the string to utf-8.

    """
    if sys.version_info[0] == 3 or (sys.version_info[0] == 2 and isinstance(string, unicode)):
        return bytes(string.encode('utf-8'))
    else:
        return bytes(string)


def compute_checksum(cell):
    m = hashlib.md5()
    # add the cell source and type
    m.update(to_bytes(cell.source))
    m.update(to_bytes(cell.cell_type))

    # add whether it's a grade cell and/or solution cell
    m.update(to_bytes(str(is_grade(cell))))
    m.update(to_bytes(str(is_solution(cell))))
    m.update(to_bytes(str(is_locked(cell))))

    # include the cell id
    m.update(to_bytes(cell.metadata.nbgrader['grade_id']))

    # include the number of points that the cell is worth, if it is a grade cell
    if is_grade(cell):
        m.update(to_bytes(str(float(cell.metadata.nbgrader['points']))))

    return m.hexdigest()


def parse_utc(ts):
    """Parses a timestamp into datetime format, converting it to UTC if necessary."""
    if ts is None:
        return None
    if isinstance(ts, six.string_types):
        parts = ts.split(" ")
        if len(parts) == 3:
            ts = " ".join(parts[:2] + ["TZ"])
            tz = parts[2]
            try:
                tz = int(tz)
            except ValueError:
                tz = dateutil.tz.gettz(tz)
            ts = dateutil.parser.parse(ts, tzinfos=dict(TZ=tz))
        else:
            ts = dateutil.parser.parse(ts)
    if ts.tzinfo is not None:
        ts = (ts - ts.utcoffset()).replace(tzinfo=None)
    return ts


def to_numeric_tz(timezone):
    """Converts a timezone to a format which can be read by parse_utc."""
    return as_timezone(datetime.utcnow(), timezone).strftime('%z')


def as_timezone(ts, timezone):
    """Converts UTC timestamp ts to have timezone tz."""
    if not timezone:
        return ts
    tz = gettz(timezone)
    if tz:
        return (ts + tz.utcoffset(ts)).replace(tzinfo=tz)
    else:
        return ts


def check_mode(path, read=False, write=False, execute=False):
    """Can the current user can rwx the path."""
    mode = 0
    if read:
        mode |= os.R_OK
    if write:
        mode |= os.W_OK
    if execute:
        mode |= os.X_OK
    return os.access(path, mode)


def check_directory(path, read=False, write=False, execute=False):
    """Does that path exist and can the current user rwx."""
    if os.path.isdir(path) and check_mode(path, read=read, write=write, execute=execute):
        return True
    else:
        return False


def get_osusername():
    """Get the username of the current process."""
    if pwd is None:
        raise OSError("get_username cannot be called on Windows")
    return pwd.getpwuid(os.getuid())[0]


def get_username():
    """ Get the username, use os user name but override if username is jovyan ."""
    osname = get_osusername()
    if osname == 'jovyan':
        return os.environ.get('JUPYTERHUB_USER', 'jovyan')
    else:
        return osname


def find_owner(path):
    """Get the username of the owner of path."""
    if pwd is None:
        raise OSError("find_owner cannot be called on Windows")
    return pwd.getpwuid(os.stat(os.path.abspath(path)).st_uid).pw_name


def self_owned(path):
    """Is the path owned by the current user of this process?"""
    return get_osusername() == find_owner(os.path.abspath(path))


def is_ignored(filename, ignore_globs=None):
    """Determines whether a filename should be ignored, based on whether it
    matches any file glob in the given list. Note that this only matches on the
    base filename itself, not the full path."""
    if ignore_globs is None:
        return False
    dirname = os.path.dirname(filename)
    for expr in ignore_globs:
        globs = glob.glob(os.path.join(dirname, expr))
        if filename in globs:
            return True
    return False


def ignore_patterns(exclude=None, include=None, max_file_size=None, log=None):
    """
    Function that can be used as :func:`shutils.copytree` ignore parameter.

    This is a generalization of :func:`shutils.ignore_patterns` that supports
    include globs, exclude globs, max file size, and logging.

    Arguments
    ---------
    exclude: list or None
        A list of filename globs or None (the default)
    include: list or None
        A list of filename globs or None (the default)
    max_file_size: int or float
        The max file size, in kilobytes
    log: logging.Logger or None (the default)

    Returns
    -------

    A function taking a directory name and list of file/directory
    names and returning the list of file/directory names to be
    ignored.

    A file/directory is ignored as soon as it is either excluded, or
    not included explicitely, or too large.

    If a logger is provided, a warning is logged for files too large
    and a debug message for otherwise ignored files.
    """
    def ignore_patterns(directory, filelist):
        ignored = []
        for filename in filelist:
            rationale = None
            fullname = os.path.join(directory, filename)
            if exclude and any(fnmatch.fnmatch(filename, glob) for glob in exclude):
                if log:
                    log.debug("Ignoring excluded file '{}' (see config option CourseDirectory.ignore)".format(fullname))
                ignored.append(filename)
            else:
                if os.path.isfile(fullname):
                    if include and not any(fnmatch.fnmatch(filename, glob) for glob in include):
                        if log:
                            log.debug("Ignoring non included file '{}' (see config option CourseDirectory.include)".format(fullname))
                        ignored.append(filename)
                    elif max_file_size and os.path.getsize(fullname) > 1000*max_file_size:
                        if log:
                            log.warning("Ignoring file too large '{}' (see config option CourseDirectory.max_file_size)".format(fullname))
                        ignored.append(filename)
        return ignored
    return ignore_patterns


def find_all_files(path, exclude=None):
    """Recursively finds all filenames rooted at `path`, optionally excluding
    some based on filename globs."""
    files = []
    to_skip = []
    for dirname, dirnames, filenames in os.walk(path):
        if is_ignored(dirname, exclude) or dirname in to_skip:
            to_skip.extend([os.path.join(dirname, x) for x in dirnames])
            continue
        for filename in filenames:
            fullpath = os.path.join(dirname, filename)
            if is_ignored(fullpath, exclude):
                continue
            else:
                files.append(fullpath)
    return files


def find_all_notebooks(path):
    """Return a sorted list of notebooks recursively found rooted at `path`."""
    notebooks = list()
    rootpath = os.path.abspath(path)
    for _file in find_all_files(rootpath):
        if os.path.splitext(_file)[-1] == '.ipynb':
            notebooks.append(os.path.relpath(_file, rootpath))
    notebooks.sort()
    return notebooks


def full_split(path):
    rest, last = os.path.split(path)
    if last == path:
        return (path,)
    elif rest == path:
        return (rest,)
    else:
        return full_split(rest) + (last,)


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    if dirname:
        os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(currdir)


@contextlib.contextmanager
def setenv(**kwargs):
    previous_env = { }
    for key, value in kwargs.items():
        previous_env[key] = os.environ.get(value)
        os.environ[key] = value
    yield
    for key, value in kwargs.items():
        if previous_env[key] is None:
            del os.environ[key]
        else:
            os.environ[key] = previous_env[key]


def rmtree(path):
    # for windows, we need to go through and make sure everything
    # is writeable, otherwise rmtree will fail
    if sys.platform == 'win32':
        for dirname, _, filenames in os.walk(path):
            os.chmod(dirname, stat.S_IWRITE)
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), stat.S_IWRITE)

    # now we can remove the path
    shutil.rmtree(path)


def remove(path):
    # for windows, we need to make sure that the file is writeable,
    # otherwise remove will fail
    if sys.platform == 'win32':
        os.chmod(path, stat.S_IWRITE)

    # now we can remove the path
    os.remove(path)


def unzip(src, dest, zip_ext=None, create_own_folder=False, tree=False):
    """Extract all content from an archive file to a destination folder.

    Arguments
    ---------
    src: str
        Absolute path to the archive file ('/path/to/archive_filename.zip')
    dest: str
        Asolute path to extract all content to ('/path/to/extract/')

    Keyword Arguments
    -----------------
    zip_ext: list
        Valid zip file extensions. Default: ['.zip', '.gz']
    create_own_folder: bool
        Create a sub-folder in 'dest' with the archive file name if True
        ('/path/to/extract/archive_filename/'). Default: False
    tree: bool
        Extract archive files within archive files (into their own
        sub-directory) if True. Default: False
    """
    zip_ext = list(zip_ext or ['.zip', '.gz'])
    filename, ext = os.path.splitext(os.path.basename(src))
    if ext not in zip_ext:
        raise ValueError("Invalid archive file extension {}: {}".format(ext, src))
    if not check_directory(dest, write=True, execute=True):
        raise OSError("Directory not found or unwritable: {}".format(dest))

    if create_own_folder:
        # double splitext for .tar.gz
        fname, ext = os.path.splitext(os.path.basename(filename))
        if ext == '.tar':
            filename = fname
        dest = os.path.join(dest, filename)
        if not os.path.isdir(dest):
            os.makedirs(dest)

    unpack_archive(src, dest, drivers=(unpack_zipfile, unpack_tarfile))

    # extract flat, don't extract archive files within archive files
    if not tree:
        return

    def find_archive_files(skip):
        found = []
        # find archive files in dest that are not in skip
        for root, _, filenames in os.walk(dest):
            for basename in filenames:
                src_file = os.path.join(root, basename)
                _, ext = os.path.splitext(basename)
                if ext in zip_ext and src_file not in skip:
                    found.append(src_file)
        return found

    skip = []
    new_files = find_archive_files(skip)
    # keep walking dest until no new archive files are found
    while new_files:
        # unzip (flat) new archive files found in dest
        for src_file in new_files:
            dest_path = os.path.split(src_file)[0]
            unzip(
                src_file,
                dest_path,
                zip_ext=zip_ext,
                create_own_folder=True,
                tree=False
            )
            skip.append(src_file)
        new_files = find_archive_files(skip)


@contextlib.contextmanager
def temp_attrs(app, **newvals):
    oldvals = {}
    for k, v in newvals.items():
        oldvals[k] = getattr(app, k)
        setattr(app, k, v)

    yield app

    for k, v in oldvals.items():
        setattr(app, k, v)


def capture_log(app, fmt="[%(levelname)s] %(message)s"):
    """Adds an extra handler to the given application the logs to a string
    buffer, calls ``app.start()``, and returns the log output. The extra
    handler is removed from the application before returning.

    Arguments
    ---------
    app: LoggingConfigurable
        An application, withh the `.start()` method implemented
    fmt: string
        A format string for formatting log messages

    Returns
    -------
    A dictionary with the following keys (error and log may or may not be present):

        - success (bool): whether or not the operation completed successfully
        - error (string): formatted traceback
        - log (string): captured log output

    """
    log_buff = six.StringIO()
    handler = logging.StreamHandler(log_buff)
    formatter = LogFormatter(fmt="[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    app.log.addHandler(handler)

    try:
        app.start()

    except:
        log_buff.flush()
        val = log_buff.getvalue()
        result = {"success": False}
        result["error"] = traceback.format_exc()
        if val:
            result["log"] = val

    else:
        log_buff.flush()
        val = log_buff.getvalue()
        result = {"success": True}
        if val:
            result["log"] = val

    finally:
        log_buff.close()
        app.log.removeHandler(handler)

    return result


def notebook_hash(path, unique_key=None):
    m = hashlib.md5()
    m.update(open(path, 'rb').read())
    if unique_key:
        m.update(to_bytes(unique_key))
    return m.hexdigest()


def make_unique_key(course_id, assignment_id, notebook_id, student_id, timestamp):
    return "+".join([
        course_id, assignment_id, notebook_id, student_id, timestamp])
