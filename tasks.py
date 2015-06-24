import os
import re
import shutil
import glob

from invoke import task
from invoke import run as _run
from copy import deepcopy
from textwrap import dedent


def run(*args, **kwargs):
    if 'pty' not in kwargs:
        kwargs['pty'] = True
    if 'echo' not in kwargs:
        kwargs['echo'] = True
    return _run(*args, **kwargs)

def echo(msg):
    print("\033[1;37m{0}\033[0m".format(msg))

def _check_if_directory_in_path(pth, target):
    while pth != '':
        pth, dirname = os.path.split(pth)
        if dirname == target:
            return True
    return False


try:
    from IPython.nbformat import read, write
    from IPython.nbconvert.preprocessors import ClearOutputPreprocessor
except ImportError:
    echo("Warning: IPython could not be imported, some tasks may not work")


@task
def check_docs_input(root='docs/source'):
    """Check that docs have output cleared."""
    echo("Checking that all docs have cleared outputs...")
    bad = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip submitted directory -- those files are allowed to have outputs
        if _check_if_directory_in_path(dirpath, 'submitted'):
            continue

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, 'r') as fh:
                    nb = read(fh, 4)

                # check notebook metadata
                if len(nb.metadata) != 0:
                    bad.append(pth)
                    continue

                # check outputs of all the cells
                for cell in nb.cells:
                    if cell.cell_type != 'code':
                        continue
                    if len(cell.outputs) != 0 or cell.execution_count is not None:
                        bad.append(pth)
                        break

    if len(bad) > 0:
        raise RuntimeError(dedent(
            """

            The following notebooks have not been properly cleared:

            {}

            Please run 'invoke clear_docs' from the root of the repository
            in order to clear the outputs of these notebooks.
            """.format(bad)
        ))


@task
def docs(root='docs'):
    """Build documentation."""
    echo("Building documentation from '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # cleanup ignored files
    run('git clean -fdX')

    # make sure all the docs have been cleared
    check_docs_input(root='source')

    # execute the docs
    run(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=source/user_guide '
        '--profile-dir=/tmp '
        'source/user_guide/*.ipynb')

    # convert to rst
    run(
        'ipython nbconvert '
        '--to rst '
        '--FilesWriter.build_directory=source/user_guide '
        '--profile-dir=/tmp '
        'source/user_guide/*.ipynb')

    # hack to convert links to ipynb files to html
    for filename in glob.glob('source/user_guide/*.ipynb'):
        filename = os.path.splitext(filename)[0] + '.rst'
        with open(filename, 'r') as fh:
            source = fh.read()
        source = re.sub(r"<([^><]*)\.ipynb>", r"<\1.html>", source)
        with open(filename, 'w') as fh:
            fh.write(source)

    # convert examples to html
    for dirname, dirnames, filenames in os.walk('source/user_guide'):
        if dirname == 'source/user_guide':
            continue
        if dirname == 'source/user_guide/images':
            continue

        build_directory = os.path.join('source', 'extra_files', os.path.relpath(dirname, 'source'))
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

@task
def clear_docs(root='docs/source'):
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
                    print("Cleared '{}'".format(pth))

@task
def publish_docs(github_token, git_name, git_email):
    echo("Publishing documentation to 'docs' branch...")

    # configure git credentials
    run("git config user.name '{}'".format(git_name.strip()))
    run("git config user.email '{}'".format(git_email.strip()))
    run("git config credential.helper 'store --file=.git/credentials'")
    with open(".git/credentials", "w") as fh:
        fh.write("https://{}:@github.com".format(github_token.strip()))
    run('shasum .git/credentials')

    # setup the remote
    run('git remote set-url --push origin https://github.com/jupyter/nbgrader.git')
    run('git remote set-branches --add origin docs')
    run('git fetch origin')
    run('git branch docs origin/docs')

    # get the current commit
    ref = run('git rev-parse HEAD', pty=False, hide=True).stdout.strip()
    commit = run('git rev-parse --short {}'.format(ref), pty=False, hide=True).stdout.strip()

    # switch to the docs branch, and get the latest version from master
    run('git checkout docs')
    run('rm -rf *')
    run('ls -a')
    run('git checkout {} -- .'.format(commit))
    run('git reset HEAD -- .travis.yml .gitignore')
    run('git checkout -- .travis.yml .gitignore')

    docs(root='docs')

    # commit the changes
    run('git add -A -f')
    run("git commit -m 'Update docs ({})'".format(commit))

    # push to origin
    run('git push -v origin docs')

@task
def python_tests(mark):
    import distutils.sysconfig
    site = distutils.sysconfig.get_python_lib()
    sitecustomize_path = os.path.join(site, "sitecustomize.py")
    if os.path.exists(sitecustomize_path):
        with open(sitecustomize_path, "r") as fh:
            sitecustomize = fh.read()
        with open(sitecustomize_path, "w") as fh:
            fh.write(re.sub(
                "^### begin nbgrader changes$.*^### end nbgrader changes$[\n]",
                "",
                sitecustomize,
                flags=re.MULTILINE | re.DOTALL))

    with open(sitecustomize_path, "a") as fh:
        fh.write(dedent(
            """
            ### begin nbgrader changes
            import coverage; coverage.process_startup()
            ### end nbgrader changes
            """
        ).lstrip())

    run('COVERAGE_PROCESS_START={} py.test -k "{}" --cov nbgrader --no-cov-on-fail -v -x --capture=no'.format(
        os.path.join(os.getcwd(), ".coveragerc"), mark))

    run("ls -a .coverage*")
    run("coverage combine")

@task
def tests(group='', python_version=None, pull_request=None, github_token="", git_name="", git_email=""):
    if group == '':
        python_tests("not js")

    elif group == 'js':
        python_tests("js")

    elif group == 'docs':
        print("Pull request is: {}".format(pull_request))
        if python_version == '3.4' and pull_request == 'false':
            publish_docs(github_token, git_name, git_email)
        else:
            docs(root='docs')

    else:
        raise ValueError("Invalid test group: {}".format(group))

@task
def after_success(group=''):
    if group in ('', 'js'):
        run('coveralls')
    else:
        echo('Nothing to do.')

@task
def js(clean=True):
    run('npm install')
    run('./node_modules/.bin/bower install --config.interactive=false')
    if clean:
        run('git clean -fdX nbgrader/html/static/components')

@task
def before_install(group='', python_version=None):
    # install testing requirements
    run('pip install nose pytest pytest-cov coverage coveralls selenium')

    # install requirements
    run('pip install -r requirements.txt')

    # install jupyterhub
    if python_version == '3.4' and group == 'js':
        os.chdir(os.environ['HOME'])
        run('npm install -g configurable-http-proxy')
        run('git clone --quiet --depth 1 https://github.com/minrk/travis-wheels travis-wheels')
        run('git clone --quiet --recursive https://github.com/jupyter/jupyterhub.git')
        os.chdir('jupyterhub')
        run('pip install -f ~/travis-wheels/wheelhouse -r dev-requirements.txt .')

    # install js dependencies
    if group == 'js':
        run('python -m IPython.external.mathjax')
