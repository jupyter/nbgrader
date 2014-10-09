from fabric.api import task, local
import os

def build():
    os.chdir('command_line_tools')
    local('ipython nbconvert --config=../ipython_nbconvert_config.py')
    os.chdir('..')

    os.chdir('user_guide')
    local('ipython nbconvert --config=../ipython_nbconvert_config.py')
    os.chdir('..')


@task
def clean():
    local('rm -f user_guide/release_example/StudentNotebook.ipynb')
    local('rm -f user_guide/grade_example/GradedNotebookBitdiddle.ipynb')

@task(default=True)
def all():
    clean()
    build()
