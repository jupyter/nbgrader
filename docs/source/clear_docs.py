import os
import sys
import subprocess as sp
from copy import deepcopy

try:
    from IPython.nbformat import read, write
    from IPython.nbconvert.preprocessors import ClearOutputPreprocessor
except ImportError:
    print("Warning: IPython could not be imported, some tasks may not work")


def echo(msg):
    print("\033[1;37m{0}\033[0m".format(msg))


def run(cmd):
    echo(cmd)
    proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = proc.communicate()
    print(stdout.decode())
    if proc.poll() != 0:
        print("Command exited with code: {}".format(proc.poll()))
        sys.exit(1)


def _check_if_directory_in_path(pth, target):
    while pth not in ('', '/'):
        pth, dirname = os.path.split(pth)
        if dirname == target:
            return True
    return False


def clear_notebooks(root):
    """Clear the outputs of documentation notebooks."""

    # cleanup ignored files
    run('git clean -fdX {}'.format(root))

    echo("Clearing outputs of notebooks in '{}'...".format(os.path.abspath(root)))
    preprocessor = ClearOutputPreprocessor()

    for dirpath, dirnames, filenames in os.walk(root):
        is_submitted = _check_if_directory_in_path(dirpath, 'submitted')

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, 'r') as fh:
                    orig_nb = read(fh, 4)

                # copy the original notebook
                new_nb = deepcopy(orig_nb)

                # check outputs of all the cells
                if not is_submitted:
                    new_nb = preprocessor.preprocess(new_nb, {})[0]

                # clear metadata
                new_nb.metadata = {}

                # write the notebook back to disk
                with open(pth, 'w') as fh:
                    write(new_nb, fh, 4)

                if orig_nb != new_nb:
                    echo("Cleared '{}'".format(pth))

if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    clear_notebooks(root)
