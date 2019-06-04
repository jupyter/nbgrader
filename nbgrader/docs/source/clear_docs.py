# -*- coding: utf-8 -*-

import io
import os
import stat
import sys
import shutil
import re
import subprocess as sp
from copy import deepcopy

try:
    from nbformat import read, write
    from nbconvert.preprocessors import ClearOutputPreprocessor
except ImportError:
    print("Warning: nbformat and/or nbconvert could not be imported, some tasks may not work")


try:
    import pwd
except:
    pwd = None


def run(cmd):
    print(" ".join(cmd))
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = proc.communicate()
    if proc.poll() != 0:
        print(stdout.decode())
        print("Command exited with code: {}".format(proc.poll()))
        sys.exit(1)


def _check_if_directory_in_path(pth, target):

    while pth not in ('', '/'):
        pth, dirname = os.path.split(pth)
        if dirname == target:
            return True
    return False


def clean_notebook_metadata(root):
    """Cleans the metadata of documentation notebooks."""

    print("Cleaning the metadata of notebooks in '{}'...".format(os.path.abspath(root)))

    for dirpath, dirnames, filenames in os.walk(root):
        is_submitted = _check_if_directory_in_path(dirpath, 'submitted')

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with io.open(pth, encoding='utf-8') as fh:
                    orig_nb = read(fh, 4)

                # copy the original notebook
                new_nb = clean_notebook(orig_nb)

                # write the notebook back to disk
                os.chmod(pth, stat.S_IRUSR | stat.S_IWUSR)
                with io.open(pth, mode='w', encoding='utf-8') as fh:
                    write(new_nb, fh, 4)

                if orig_nb != new_nb:
                    print("Cleaned '{}'".format(pth))


def clear_notebooks(root):
    """Clear the outputs of documentation notebooks."""

    # cleanup ignored files
    run(['git', 'clean', '-fdX', root])

    # remove release/autograded/feedback
    if os.path.exists(os.path.join(root, "user_guide", "release")):
        shutil.rmtree(os.path.join(root, "user_guide", "release"))
    if os.path.exists(os.path.join(root, "user_guide", "autograded")):
        shutil.rmtree(os.path.join(root, "user_guide", "autograded"))
    if os.path.exists(os.path.join(root, "user_guide", "feedback")):
        shutil.rmtree(os.path.join(root, "user_guide", "feedback"))
    if os.path.exists(os.path.join(root, "user_guide", "downloaded", "ps1", "extracted")):
        shutil.rmtree(os.path.join(root, "user_guide", "downloaded", "ps1", "extracted"))

    print("Clearing outputs of notebooks in '{}'...".format(os.path.abspath(root)))
    preprocessor = ClearOutputPreprocessor()

    for dirpath, dirnames, filenames in os.walk(root):
        is_submitted = _check_if_directory_in_path(dirpath, 'submitted')

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with io.open(pth, encoding='utf-8') as fh:
                    orig_nb = read(fh, 4)

                # copy the original notebook
                new_nb = clean_notebook(orig_nb)

                # check outputs of all the cells
                if not is_submitted:
                    new_nb = preprocessor.preprocess(new_nb, {})[0]

                # write the notebook back to disk
                with io.open(pth, mode='w', encoding='utf-8') as fh:
                    write(new_nb, fh, 4)

                if orig_nb != new_nb:
                    print("Cleared '{}'".format(pth))


def clean_notebook(orig_nb):
    new_nb = deepcopy(orig_nb)
    clean_metadata(new_nb)
    return new_nb


def clean_metadata(new_nb):
    new_nb.metadata = {
        "kernelspec": {
            "display_name": "Python",
            "language": "python",
            "name": "python"
        }
    }


def sanitize_notebook():
    if pwd:
        user = pwd.getpwuid(os.getuid())[0]
    else:
        user = "username"
    root = os.path.abspath(os.path.dirname(__file__))
    nb_root = '/'.join(root.split('/')[:-3])
    for dirpath, _, filenames in os.walk(root):
        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, encoding='utf-8') as fh:
                    orig_nb = fh.read()

                # copy the original notebook
                new_nb = orig_nb.replace(nb_root, '[NB_GRADER_ROOT]')
                # parses: permissions, links, user, group, size, month, day, time
                new_nb = re.sub(r'([-drwxs][-rwxs]{9}\.?)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(\w+)\s+(\d)+\s+(\d\d:\d\d)', r'\1 1 nb_user nb_group [size] [date] [time]', new_nb)
                # parses: permissions, links, user, group, size, month, day, year
                new_nb = re.sub(r'([-drwxs][-rwxs]{9}\.?)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(\w+)\s+(\d)+\s+(\d+)', r'\1 1 nb_user nb_group [size] [date] [time]', new_nb)
                new_nb = re.sub(r'"total \d+\\n"', r'"total ##\\n"', new_nb)
                new_nb = re.sub(r'\d\d\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d\.\d\d\d\d\d\d', r'[timestamp]', new_nb)
                new_nb = re.sub(r'(example_course )\w+( ps1 \[timestamp\] UTC)', r'\1nb_user\2', new_nb)
                new_nb = re.sub(r'(inbound/)\w+(\+\w+\+\[timestamp\] UTC\+)([^\\]+)\\n', r'\1nb_user\2[random string]\\n', new_nb)
                new_nb = re.sub(r'"(\[CollectApp \| INFO\] Collecting submission:\s+)\w+(\s+\w+\\n)"', r'"\1nb_user\2"', new_nb)
                new_nb = re.sub(r'([-drwxs][-rwxs]{9}\.?\s+1\s+nb_user\s+nb_group\s+\[size\]\s+\[date\]\s+\[time\]\s+)%s(\\n")' % user, r'\1nb_user\2', new_nb)
                new_nb = re.sub(r'\s+"[-drwxs][-rwxs]{9}\.?\s+1\s+nb_user\s+nb_group\s+\[size\]\s+\[date\]\s+\[time\]\s+Library\\n",', r'', new_nb)
                new_nb = re.sub(r'/private/tmp', r'/tmp', new_nb)
                new_nb = re.sub(r'Writing [0-9]+ bytes', r'Writing [size] bytes', new_nb)
                new_nb = re.sub(r'([-drwxs][-rwxs]{9})\.', r'\1', new_nb)
                new_nb = re.sub(r'([-drwxs][-rwxs]{9})\.', r'\1', new_nb)

                if orig_nb != new_nb:
                    with open(pth, 'w', encoding='utf-8') as fh:
                        fh.write(new_nb)
                    print("sanitized {}".format(filename))
                else:
                    print("nothing to sanitize in {}".format(filename))


if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    clean_notebook_metadata(root)
    sanitize_notebook()
