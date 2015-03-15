import os
from invoke import task
from invoke import run as _run

def run(*args, **kwargs):
    if 'pty' not in kwargs:
        kwargs['pty'] = True
    return _run(*args, **kwargs)

@task
def docs():
    # cleanup, just to be safe
    run('rm -rf user_guide/release_example/student')
    run('rm -rf user_guide/grade_example/autograded')

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

@task
def publish_docs(github_token, git_name, git_email):
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

    docs()

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
        if python_version == '3.4' and pull_request == 'false':
            publish_docs(github_token, git_name, git_email)
        else:
            docs()

    else:
        raise ValueError("Invalid test group: {}".format(group))

@task
def after_success(group='', python_version=None, pull_request=None):
    if group == 'docs' and python_version == '3.4' and pull_request == 'false':
        run('git checkout docs')
        run('git push origin docs')
    elif group == '' and python_version == '3.4':
        run('coveralls')
