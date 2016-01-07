import os
import re

from invoke import task
from invoke import run as _run
from textwrap import dedent


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


try:
    from nbformat import read
except ImportError:
    echo("Warning: nbformat could not be imported, some tasks may not work")


@task
def check_docs_input(root='docs/source'):
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
def docs():
    check_docs_input()
    run('make -C docs html')


@task
def clear_docs():
    run('python docs/source/clear_docs.py')


def _run_tests(mark=None, skip=None):
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

    cmd = [
        'COVERAGE_PROCESS_START={}'.format(os.path.join(os.getcwd(), ".coveragerc")),
        'py.test',
        '--cov nbgrader',
        '--no-cov-on-fail',
        '-v',
        '-x'
    ]

    marks = []
    if mark is not None:
        marks.append(mark)
    if skip is not None:
        marks.append("not {}".format(skip))
    if len(marks) > 0:
        cmd.append('-m "{}"'.format(" and ".join(marks)))

    run(" ".join(cmd))
    run("ls -a .coverage*")
    run("coverage combine")


@task
def tests(group='all', skip=None):
    if group == 'python':
        _run_tests(mark="not js", skip=skip)

    elif group == 'js':
        _run_tests(mark="js", skip=skip)

    elif group == 'docs':
        docs()

    elif group == 'all':
        _run_tests(skip=skip)

    else:
        raise ValueError("Invalid test group: {}".format(group))


@task
def after_success(group):
    if group in ('python', 'js'):
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
    if python_version == '3.4' and group == 'js':
        run('npm install -g configurable-http-proxy')
        run('pip install jupyterhub')


@task
def install(group):
    cmd = 'pip install -r dev-requirements.txt -e .'
    run('PIP_FIND_LINKS=~/travis-wheels/wheelhouse {}'.format(cmd))
