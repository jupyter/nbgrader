from fabric.api import task, local
import os
import glob

def build():
    os.chdir('command_line_tools')
    local('ipython nbconvert --to notebook --execute --inplace --profile-dir=/tmp *.ipynb')
    os.chdir('..')

    os.chdir('user_guide')
    local('ipython nbconvert --to notebook --execute --inplace --profile-dir=/tmp *.ipynb')
    os.chdir('..')


@task
def clean():
    local('rm -rf user_guide/release_example/student')
    local('rm -rf user_guide/grade_example/autograded')

@task(default=True)
def all():
    clean()
    build()
