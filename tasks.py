from invoke import run, task

@task
def docs(branch='master'):
    # get the current commit on master
    commit = run('git rev-parse --short {}'.format(branch)).stdout.strip()

    # switch to the docs branch, and get the latest version from master
    run('git checkout docs')
    run('rm -r *')
    run('git checkout {} -- docs'.format(branch))
    run('mv docs/* . && rmdir docs')

    # cleanup, just to be save
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

    # commit the changes
    run('git add -A -f')
    run('git commit -m "Update docs ({} version {})"'.format(branch, commit))

    # switch back to master
    run('git checkout {}'.format(branch))
