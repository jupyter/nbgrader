import os
import hashlib
import dateutil.parser
import glob
import six
import sys
import shutil
import stat

# pwd is for unix passwords only, so we shouldn't import it on
# windows machines
if sys.platform != 'win32':
    import pwd
else:
    pwd = None


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

def determine_grade(cell):
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
        for output in cell.outputs:
            if output.output_type == 'error':
                return 0, max_points
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
        ts = dateutil.parser.parse(ts)
    if ts.tzinfo is not None:
        ts = (ts - ts.utcoffset()).replace(tzinfo=None)
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

def get_username():
    """Get the username of the current process."""
    if pwd is None:
        raise OSError("get_username cannot be called on Windows")
    return pwd.getpwuid(os.getuid())[0]

def find_owner(path):
    """Get the username of the owner of path."""
    if pwd is None:
        raise OSError("find_owner cannot be called on Windows")
    return pwd.getpwuid(os.stat(os.path.abspath(path)).st_uid).pw_name

def self_owned(path):
    """Is the path owned by the current user of this process?"""
    return get_username() == find_owner(os.path.abspath(path))

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

def find_all_files(path, exclude=None):
    """Recursively finds all filenames rooted at `path`, optionally excluding
    some based on filename globs."""
    files = []
    for dirname, dirnames, filenames in os.walk(path):
        if is_ignored(dirname, exclude):
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
