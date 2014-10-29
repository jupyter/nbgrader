from fabric.api import task, local
import os
import glob

def build():
    os.chdir('command_line_tools')
    for filename in glob.glob("*.ipynb"):
        basename = os.path.splitext(filename)[0]
        local('ipython nbconvert --config=../ipython_nbconvert_config.py --profile-dir=/tmp --output "{}" "{}"'.format(basename, filename))
    os.chdir('..')

    os.chdir('user_guide')
    for filename in glob.glob("*.ipynb"):
        basename = os.path.splitext(filename)[0]
        local('ipython nbconvert --config=../ipython_nbconvert_config.py --profile-dir=/tmp --output "{}" "{}"'.format(basename, filename))
    os.chdir('..')


@task
def clean():
    local('rm -f user_guide/release_example/StudentNotebook.ipynb')
    local('rm -f user_guide/grade_example/GradedNotebookBitdiddle.ipynb')
    local('rm -f user_guide/grade_example/GradedNotebookBitdiddle.html')

@task(default=True)
def all():
    clean()
    build()
