import re
import os
from fabric.api import task, local

@task
def docs(branch='master', default=True):
    # get the current commit on master
    commit = local('git rev-parse --short {}'.format(branch), capture=True)

    # switch to the docs branch, and get the latest version from master
    local('git checkout docs')
    local('rm -r *')
    local('git checkout {} -- docs'.format(branch))
    local('mv docs/* . && rmdir docs')

    # cleanup, just to be save
    local('rm -rf user_guide/release_example/student')
    local('rm -rf user_guide/grade_example/autograded')

    # build the docs
    local(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=command_line_tools '
        '--profile-dir=/tmp '
        'command_line_tools/*.ipynb')
    local(
        'ipython nbconvert '
        '--to notebook '
        '--execute '
        '--FilesWriter.build_directory=user_guide '
        '--profile-dir=/tmp '
        'user_guide/*.ipynb')

    # commit the changes
    local('git add -A -f')
    local('git commit -m "Update docs ({} version {})"'.format(branch, commit))

    # switch back to master
    local('git checkout {}'.format(branch))

@task
def travis_docs():
    repo = local('git config remote.origin.url', capture=True)
    repo = re.sub("^git://", "https://#{}@".format(os.environ['GH_TOKEN']), repo)
    branch = local('git rev-parse --abbrev-ref HEAD', capture=True)

    local('git config user.name "{}"'.format(os.environ['GIT_NAME']))
    local('git config user.email "{}"'.format(os.environ['GIT_EMAIL']))

    docs(branch=branch)
    local('git push {} {}:{}'.format(repo, branch, branch))
