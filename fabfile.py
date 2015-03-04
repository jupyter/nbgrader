from fabric.api import task, local

def build():
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

@task
def clean():
    local('rm -rf user_guide/release_example/student')
    local('rm -rf user_guide/grade_example/autograded')

@task(default=True)
def all():
    clean()
    build()

@task
def docs(branch='master'):
    # get the current commit on master
    commit = local('git rev-parse --short {}'.format(branch), capture=True)

    # switch to the docs branch, and get the latest version from master
    local('git checkout docs')
    local('rm -r *')
    local('git checkout {} -- docs'.format(branch))
    local('mv docs/* . && rmdir docs')

    # build the docs
    clean()
    build()

    # commit the changes
    local('git add -A -f')
    local('git commit -m "Update docs ({} version {})"'.format(branch, commit))

    # switch back to master
    local('git checkout {}'.format(branch))
