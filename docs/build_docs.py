import subprocess as sp
import os
import glob
import re
import shutil
import sys


def echo(msg):
    print("\033[1;37m{0}\033[0m".format(msg))


def run(cmd):
    echo(cmd)
    proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = proc.communicate()
    print(stdout.decode())
    if proc.poll() != 0:
        print("Command exited with code: {}".format(proc.poll()))


def build_docs(root='.'):
    """Build documentation."""
    echo("Building documentation from '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # cleanup ignored files
    run('git clean -fdX {}'.format(root))

    # execute the docs
    run(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=user_guide '
        '--profile-dir=/tmp '
        'user_guide/*.ipynb')

    # convert to rst
    run(
        'ipython nbconvert '
        '--to rst '
        '--FilesWriter.build_directory=user_guide '
        '--profile-dir=/tmp '
        'user_guide/*.ipynb')

    # hack to convert links to ipynb files to html
    for filename in glob.glob('user_guide/*.ipynb'):
        filename = os.path.splitext(filename)[0] + '.rst'
        with open(filename, 'r') as fh:
            source = fh.read()
        source = re.sub(r"<([^><]*)\.ipynb>", r"<\1.html>", source)
        with open(filename, 'w') as fh:
            fh.write(source)

    # convert examples to html
    for dirname, dirnames, filenames in os.walk('user_guide'):
        if dirname == 'user_guide':
            continue
        if dirname == 'user_guide/images':
            continue

        build_directory = os.path.join('extra_files', dirname)
        if not os.path.exists(build_directory):
            os.makedirs(build_directory)

        for filename in filenames:
            if filename.endswith('.ipynb'):
                run(
                    "ipython nbconvert "
                    "--to html "
                    "--FilesWriter.build_directory='{}' "
                    "--profile-dir=/tmp "
                    "'{}'".format(build_directory, os.path.join(dirname, filename)))

            else:
                shutil.copy(
                    os.path.join(dirname, filename),
                    os.path.join(build_directory, filename))

    os.chdir(cwd)


if __name__ == "__main__":
    try:
        root = os.path.dirname(__file__)
    except NameError:
        root = os.path.dirname(os.getcwd())
    build_docs(os.path.join(os.path.abspath(root), 'source'))
