import os
import re

from invoke import task
from invoke import run as _run
from textwrap import dedent

import sys
if sys.platform == 'win32':
    WINDOWS = True
else:
    WINDOWS = False


def run(*args, **kwargs):
    if 'pty' not in kwargs:
        kwargs['pty'] = True
    if WINDOWS:
        kwargs['pty'] = False
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
    from nbformat import read
except ImportError:
    echo("Warning: nbformat could not be imported, some tasks may not work")


@task
def docs():
    run('python nbgrader/docs/source/build_docs.py')
    run('make -C nbgrader/docs html')
    run('make -C nbgrader/docs linkcheck')
    run('make -C nbgrader/docs spelling')


def _run_tests(mark=None, skip=None):
    if not WINDOWS:
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

    cmd = []
    if not WINDOWS:
        cmd.append('COVERAGE_PROCESS_START={}'.format(os.path.join(os.getcwd(), ".coveragerc")))
    cmd.append('py.test')
    if not WINDOWS:
        cmd.append('--cov nbgrader')
        cmd.append('--no-cov-on-fail')
    cmd.append('-v')
    cmd.append('-x')

    marks = []
    if mark is not None:
        marks.append(mark)
    if skip is not None:
        marks.append("not {}".format(skip))
    if len(marks) > 0:
        cmd.append('-m "{}"'.format(" and ".join(marks)))

    run(" ".join(cmd))

    if not WINDOWS:
        run("ls -a .coverage*")
        run("coverage combine")


@task
def tests(group='all', skip=None):
    if group == 'python':
        _run_tests(mark="not formgrader and not nbextensions", skip=skip)

    elif group == 'formgrader':
        _run_tests(mark="formgrader", skip=skip)

    elif group == 'nbextensions':
        _run_tests(mark="nbextensions", skip=skip)

    elif group == 'docs':
        docs()

    elif group == 'all':
        _run_tests(skip=skip)

    else:
        raise ValueError("Invalid test group: {}".format(group))


@task
def after_success(group):
    if group in ('python', 'formgrader', 'nbextensions'):
        run('codecov')
    else:
        echo('Nothing to do.')


@task
def js(clean=True):
    run('npm install')
    run('./node_modules/.bin/bower install --config.interactive=false')
    if clean:
        run('git clean -fdX nbgrader/formgrader/static/components')


@task
def before_install(group, python_version):
    # clone travis wheels repo to make installing requirements easier
    run('git clone --quiet --depth 1 https://github.com/minrk/travis-wheels ~/travis-wheels')

    # install jupyterhub
    if python_version.startswith('3') and group == 'formgrader':
        run('npm install -g configurable-http-proxy')
        run('pip install jupyterhub')


@task
def install(group):
    # The docs don't seem to build correctly if it's a symlinked install.
    if group == 'docs':
        cmd = 'pip install -r dev-requirements.txt .'
    else:
        cmd = 'pip install -r dev-requirements.txt -e .'
    run('PIP_FIND_LINKS=~/travis-wheels/wheelhouse {}'.format(cmd))
