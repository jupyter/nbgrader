import os
from invoke import task
from invoke import run as _run
from copy import deepcopy
from textwrap import dedent

from IPython.nbformat import read, write
from IPython.nbconvert.preprocessors import ClearOutputPreprocessor

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

@task
def check_docs_input(root='.'):
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
def check_docs_output(root='.'):
    """Check that none of the cells in the documentation has errors."""

    error_msg = dedent(
        """

        Notebook '{}' was not successfully executed. The cell that failed was:

        ```
        {}
        ```

        It generated the following output:

        {}

        The actual error was:

        {}
        """
    )

    echo("Checking that all docs were successfully executed...")
    for dirpath, dirnames, filenames in os.walk(root):
        # skip example directory -- those files are allowed to have errors
        if _check_if_directory_in_path(dirpath, 'release_example'):
            continue
        if _check_if_directory_in_path(dirpath, 'grade_example'):
            continue

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, 'r') as fh:
                    nb = read(fh, 4)

                # check outputs of all the cells
                for cell in nb.cells:
                    if cell.cell_type != 'code':
                        continue

                    error = ""
                    stdout = ""
                    for output in cell.outputs:
                        if output.output_type == 'error':
                            error = "\n".join(output.traceback)
                        elif output.output_type == 'stream':
                            stdout += output.text

                    if error != "":
                        raise RuntimeError(error_msg.format(
                            pth, cell.source, stdout, error))

@task
def docs(root='docs'):
    """Build documentation."""
    echo("Building documentation from '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # cleanup ignored files
    run('git clean -fdX docs')

    # make sure all the docs have been cleared
    check_docs_input(root='.')

    # build the docs
    run(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=command_line_tools '
        '--profile-dir=/tmp '
        'command_line_tools/*.ipynb')
    run(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=user_guide '
        '--profile-dir=/tmp '
        'user_guide/*.ipynb')

    # make sure the notebooks were executed successfully
    check_docs_output(root='.')

    os.chdir(cwd)

@task
def clear_docs(root='docs'):
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

    # setup the remote
    run('git remote set-url --push origin https://github.com/jupyter/nbgrader.git')
    run('git remote set-branches --add origin docs')
    run('git fetch -q')
    run('git branch docs origin/docs')

    # configure git credentials
    run('git config user.name "{}"'.format(git_name))
    run('git config user.email "{}"'.format(git_email))
    run('git config credential.helper "store --file=.git/credentials"')
    run('echo "https://{}:@github.com" > .git/credentials'.format(github_token))

    # get the current commit
    ref = run('git rev-parse HEAD', pty=False, hide=True).stdout.strip()
    commit = run('git rev-parse --short {}'.format(ref), pty=False, hide=True).stdout.strip()

    # switch to the docs branch, and get the latest version from master
    run('git checkout docs')
    run('rm -r *')
    run('git checkout {} -- docs'.format(commit))
    run('mv docs/* . && rmdir docs')

    docs(root='.')

    # commit the changes
    run('git add -A -f')
    run('git commit -m "Update docs ({})"'.format(commit))

    # switch back to master
    run('git checkout {}'.format(ref))

@task
def python_tests():
    run("nosetests --with-coverage --cover-package nbgrader")

@task
def js_tests():
    run("iptest js/{}".format(os.path.abspath("nbgrader/tests/js")))

@task
def tests(group='', python_version=None, pull_request=None, github_token=None, git_name=None, git_email=None):
    if group == '':
        python_tests()

    elif group == 'js':
        js_tests()

    elif group == 'docs':
        print("Pull request is: {}".format(pull_request))
        if python_version == '3.4' and pull_request == 'false':
            publish_docs(github_token, git_name, git_email)
        else:
            docs(root='docs')

    else:
        raise ValueError("Invalid test group: {}".format(group))

@task
def after_success(group='', python_version=None, pull_request=None):
    if group == 'docs' and python_version == '3.4' and pull_request == 'false':
        run('git checkout docs')
        run('git push origin docs')
    elif group == '' and python_version == '3.4':
        run('coveralls')
    else:
        echo('Nothing to do.')
