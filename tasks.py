import os
import re

from invoke import task, collection
from textwrap import dedent

import sys
if sys.platform == 'win32':
    WINDOWS = True
else:
    WINDOWS = False


def run(ctx, *args, **kwargs):
    if 'pty' not in kwargs:
        kwargs['pty'] = True
    if WINDOWS:
        kwargs['pty'] = False
    if 'echo' not in kwargs:
        kwargs['echo'] = True
    return ctx.run(*args, **kwargs)

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
def docs(ctx):
    run(ctx, 'python nbgrader/docs/source/build_docs.py')
    run(ctx, 'make -C nbgrader/docs html')
    run(ctx, 'make -C nbgrader/docs linkcheck')
    run(ctx, 'make -C nbgrader/docs spelling')


@task
def clean_docs(ctx):
    run(ctx, 'python nbgrader/docs/source/clear_docs.py')


def _run_tests(ctx, mark=None, skip=None, junitxml=None):
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
    if junitxml:
        cmd.extend(['--junitxml', junitxml])
    cmd.append('-v')
    cmd.append('-x')
    cmd.extend(['--rerun', '4'])

    marks = []
    if mark is not None:
        marks.append(mark)
    if skip is not None:
        marks.append("not {}".format(skip))
    if len(marks) > 0:
        cmd.append('-m "{}"'.format(" and ".join(marks)))

    run(ctx, " ".join(cmd))

    if not WINDOWS:
        run(ctx, "ls -a .coverage*")
        run(ctx, "coverage combine || true")


@task
def tests(ctx, group='all', skip=None, junitxml=None):
    if group == 'python':
        _run_tests(ctx, mark="not nbextensions", skip=skip, junitxml=junitxml)

    elif group == 'nbextensions':
        _run_tests(ctx, mark="nbextensions", skip=skip, junitxml=junitxml)

    elif group == 'docs':
        docs(ctx)

    elif group == 'all':
        _run_tests(ctx, skip=skip, junitxml=junitxml)

    else:
        raise ValueError("Invalid test group: {}".format(group))


@task
def after_success(ctx, group):
    if group in ('python', 'nbextensions'):
        run(ctx, 'codecov')
    else:
        echo('Nothing to do.')


@task
def js(ctx, clean=True):
    run(ctx, 'npm install')
    run(ctx, './node_modules/.bin/bower install --config.interactive=false')
    if clean:
        run(ctx, 'git clean -fdX nbgrader/server_extensions/formgrader/static/components')


@task
def install(ctx, group):
    # The docs don't seem to build correctly if it's a symlinked install.
    if group == 'docs':
        cmd = 'pip install -r dev-requirements.txt .'
    else:
        cmd = 'pip install -r dev-requirements.txt -e .'

    # clone travis wheels repo to make installing requirements easier
    run(ctx, 'git clone --quiet --depth 1 https://github.com/minrk/travis-wheels ~/travis-wheels')
    run(ctx, 'PIP_FIND_LINKS=~/travis-wheels/wheelhouse {}'.format(cmd))


ns = collection.Collection(
    after_success,
    clean_docs,
    docs,
    install,
    js,
    tests,
)

if WINDOWS:
    ns.configure({
        'run': {
            'shell': os.environ.get('COMSPEC', os.environ.get('SHELL')),
        }
    })
